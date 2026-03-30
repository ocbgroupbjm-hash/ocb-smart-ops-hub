import React, { useState, useEffect, useCallback } from 'react';
import { 
  Wallet, RefreshCw, Plus, DollarSign, AlertTriangle, CheckCircle2,
  Clock, XCircle, Calendar, User, Building2, ArrowRight, X, 
  CreditCard, TrendingUp, TrendingDown, Receipt, BanknoteIcon
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

import { getApiUrl } from '../utils/apiConfig';
const API_URL = getApiUrl();

// Status Badge
const StatusBadge = ({ status }) => {
  const styles = {
    open: 'bg-green-500/20 text-green-300 border-green-500/30',
    closing: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    closed: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
    reviewed: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    discrepancy: 'bg-red-500/20 text-red-300 border-red-500/30',
    pending: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    resolved: 'bg-purple-500/20 text-purple-300 border-purple-500/30'
  };
  
  const labels = {
    open: 'Open',
    closing: 'Closing',
    closed: 'Closed',
    reviewed: 'Reviewed',
    discrepancy: 'Discrepancy',
    pending: 'Pending',
    resolved: 'Resolved'
  };
  
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded border ${styles[status] || styles.closed}`}>
      {labels[status] || status}
    </span>
  );
};

// Discrepancy Badge
const DiscrepancyBadge = ({ type }) => {
  if (type === 'none') return null;
  
  const styles = {
    shortage: 'bg-red-500/20 text-red-300',
    overage: 'bg-blue-500/20 text-blue-300'
  };
  
  const icons = {
    shortage: <TrendingDown className="h-3 w-3" />,
    overage: <TrendingUp className="h-3 w-3" />
  };
  
  return (
    <span className={`flex items-center gap-1 px-2 py-0.5 text-xs rounded ${styles[type]}`}>
      {icons[type]}
      {type === 'shortage' ? 'Kurang' : 'Lebih'}
    </span>
  );
};

// Open Shift Modal
const OpenShiftModal = ({ onClose, onSave, token, branches }) => {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    branch_id: '',
    initial_cash: 0,
    notes: ''
  });

  const handleSubmit = async () => {
    if (!form.branch_id) {
      alert('Pilih cabang terlebih dahulu');
      return;
    }
    
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/cash-control/shift/open`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(form)
      });
      
      const data = await res.json();
      
      if (data.success) {
        alert(`Shift ${data.shift.shift_no} opened`);
        onSave();
      } else {
        throw new Error(data.detail || 'Gagal buka shift');
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
          <h3 className="text-lg font-semibold text-amber-100">Buka Shift Kasir</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Cabang</label>
            <select
              value={form.branch_id}
              onChange={(e) => setForm({...form, branch_id: e.target.value})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              data-testid="branch-select"
            >
              <option value="">Pilih Cabang...</option>
              {branches.map(b => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Modal Awal (Rp)</label>
            <input
              type="number"
              value={form.initial_cash}
              onChange={(e) => setForm({...form, initial_cash: parseFloat(e.target.value) || 0})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              placeholder="0"
              data-testid="initial-cash-input"
            />
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Catatan</label>
            <input
              type="text"
              value={form.notes}
              onChange={(e) => setForm({...form, notes: e.target.value})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              placeholder="Catatan shift..."
            />
          </div>
        </div>
        
        <div className="p-6 border-t border-red-900/30 flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-amber-100">
            Batal
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg disabled:opacity-50"
            data-testid="open-shift-btn"
          >
            <Clock className="h-4 w-4" />
            {loading ? 'Opening...' : 'Buka Shift'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Close Shift Modal
const CloseShiftModal = ({ shift, onClose, onSave, token }) => {
  const [loading, setLoading] = useState(false);
  const [actualCash, setActualCash] = useState(0);
  const [notes, setNotes] = useState('');
  const [expectedData, setExpectedData] = useState(null);

  useEffect(() => {
    const fetchExpected = async () => {
      try {
        const res = await fetch(`${API_URL}/api/cash-control/shift/${shift.id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        setExpectedData(data.calculation);
        setActualCash(data.calculation?.expected_cash || 0);
      } catch (err) {
        console.error(err);
      }
    };
    fetchExpected();
  }, [shift.id, token]);

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/cash-control/shift/${shift.id}/close`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ actual_cash: actualCash, notes })
      });
      
      const data = await res.json();
      
      if (data.success) {
        const msg = data.discrepancy_type === 'none' 
          ? 'Shift closed successfully' 
          : `Shift closed with ${data.discrepancy_type}: Rp ${Math.abs(data.discrepancy).toLocaleString('id-ID')}`;
        alert(msg);
        onSave();
      } else {
        throw new Error(data.detail || 'Gagal tutup shift');
      }
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const discrepancy = actualCash - (expectedData?.expected_cash || 0);

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl max-w-lg w-full">
        <div className="p-6 border-b border-red-900/30 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-amber-100">Tutup Shift {shift.shift_no}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          {/* Expected Breakdown */}
          {expectedData && (
            <div className="bg-black/30 rounded-lg p-4 space-y-2">
              <h4 className="text-sm font-medium text-gray-400 mb-2">Perhitungan Sistem</h4>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Modal Awal:</span>
                <span className="text-gray-300">Rp {expectedData.initial_cash?.toLocaleString('id-ID')}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Penjualan Tunai:</span>
                <span className="text-green-400">+ Rp {expectedData.cash_sales?.toLocaleString('id-ID')}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Kas Masuk Lain:</span>
                <span className="text-blue-400">+ Rp {expectedData.cash_in?.toLocaleString('id-ID')}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Kas Keluar:</span>
                <span className="text-red-400">- Rp {expectedData.cash_out?.toLocaleString('id-ID')}</span>
              </div>
              <div className="border-t border-red-900/30 pt-2 flex justify-between">
                <span className="text-amber-100 font-medium">Expected Cash:</span>
                <span className="text-amber-100 font-bold">Rp {expectedData.expected_cash?.toLocaleString('id-ID')}</span>
              </div>
            </div>
          )}
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Kas Aktual (Rp)</label>
            <input
              type="number"
              value={actualCash}
              onChange={(e) => setActualCash(parseFloat(e.target.value) || 0)}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100 text-lg font-bold"
              data-testid="actual-cash-input"
            />
          </div>
          
          {/* Discrepancy Preview */}
          <div className={`p-3 rounded-lg ${discrepancy === 0 ? 'bg-green-900/20' : discrepancy < 0 ? 'bg-red-900/20' : 'bg-blue-900/20'}`}>
            <div className="flex justify-between">
              <span className="text-gray-400">Selisih:</span>
              <span className={`font-bold ${discrepancy === 0 ? 'text-green-400' : discrepancy < 0 ? 'text-red-400' : 'text-blue-400'}`}>
                {discrepancy >= 0 ? '+' : ''}Rp {discrepancy.toLocaleString('id-ID')}
              </span>
            </div>
            {Math.abs(discrepancy) > 1000 && (
              <p className="text-xs text-gray-500 mt-1">
                {discrepancy < 0 ? 'SHORTAGE - Kas kurang dari seharusnya' : 'OVERAGE - Kas lebih dari seharusnya'}
              </p>
            )}
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Catatan</label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              placeholder="Catatan penutupan..."
            />
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
            data-testid="close-shift-btn"
          >
            <XCircle className="h-4 w-4" />
            {loading ? 'Closing...' : 'Tutup Shift'}
          </button>
        </div>
      </div>
    </div>
  );
};

const CashControl = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('shifts');
  
  // Data states
  const [dashboard, setDashboard] = useState(null);
  const [shifts, setShifts] = useState([]);
  const [discrepancies, setDiscrepancies] = useState([]);
  const [deposits, setDeposits] = useState([]);
  const [currentShift, setCurrentShift] = useState(null);
  const [branches, setBranches] = useState([]);
  
  // Filter states
  const [filterStatus, setFilterStatus] = useState('');
  const [filterDate, setFilterDate] = useState(new Date().toISOString().slice(0, 10));
  
  // Modals
  const [showOpenShift, setShowOpenShift] = useState(false);
  const [shiftToClose, setShiftToClose] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (filterStatus) params.append('status', filterStatus);
      if (filterDate) {
        params.append('date_from', filterDate);
        params.append('date_to', filterDate);
      }
      
      const [dashRes, shiftsRes, discRes, depRes, currentRes, branchRes] = await Promise.all([
        fetch(`${API_URL}/api/cash-control/dashboard/summary?date=${filterDate}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/cash-control/shifts?${params}&limit=50`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/cash-control/discrepancies?status=pending`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/cash-control/deposits?date_from=${filterDate}&date_to=${filterDate}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/cash-control/shift/current`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/branches`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      
      const [dashData, shiftsData, discData, depData, currentData, branchData] = await Promise.all([
        dashRes.json(),
        shiftsRes.json(),
        discRes.json(),
        depRes.json(),
        currentRes.json(),
        branchRes.json()
      ]);
      
      setDashboard(dashData);
      setShifts(shiftsData.items || []);
      setDiscrepancies(discData.items || []);
      setDeposits(depData.items || []);
      setCurrentShift(currentData.has_open_shift ? currentData.shift : null);
      setBranches(branchData.items || branchData || []);
      
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, filterStatus, filterDate]);

  useEffect(() => {
    if (token) fetchData();
  }, [token, fetchData]);

  const handleResolveDiscrepancy = async (discrepancyId) => {
    const resolutionType = prompt('Resolution type (explained/written_off/recovered):', 'explained');
    if (!resolutionType) return;
    
    const notes = prompt('Resolution notes:', '');
    if (notes === null) return;
    
    try {
      const res = await fetch(`${API_URL}/api/cash-control/discrepancy/${discrepancyId}/resolve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ resolution_type: resolutionType, resolution_notes: notes })
      });
      
      const data = await res.json();
      
      if (data.success) {
        alert('Discrepancy resolved');
        fetchData();
      }
    } catch (err) {
      alert('Gagal resolve');
    }
  };

  return (
    <div className="space-y-6" data-testid="cash-control-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Deposit & Cash Control</h1>
          <p className="text-gray-400 text-sm mt-1">Monitoring setoran kasir dan selisih kas</p>
        </div>
        <div className="flex gap-2">
          {!currentShift ? (
            <button
              onClick={() => setShowOpenShift(true)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg"
              data-testid="open-shift-btn"
            >
              <Plus className="h-4 w-4" />
              Buka Shift
            </button>
          ) : (
            <button
              onClick={() => setShiftToClose(currentShift)}
              className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg"
              data-testid="close-shift-btn"
            >
              <XCircle className="h-4 w-4" />
              Tutup Shift
            </button>
          )}
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-red-900/30 hover:bg-red-900/50 text-amber-100 rounded-lg"
            data-testid="refresh-btn"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Current Shift Banner */}
      {currentShift && (
        <div className="bg-gradient-to-r from-green-900/30 to-green-800/10 border border-green-700/30 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-green-500/20 flex items-center justify-center">
                <Clock className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-green-100 font-semibold">Shift Aktif: {currentShift.shift_no}</p>
                <p className="text-green-400 text-sm">Mulai: {new Date(currentShift.start_time).toLocaleString('id-ID')}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-gray-400 text-sm">Expected Cash</p>
              <p className="text-green-100 text-xl font-bold">Rp {currentShift.expected_cash?.toLocaleString('id-ID') || '0'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Summary */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/10 border border-blue-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Clock className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-lg font-bold text-blue-300">{dashboard.shifts?.open || 0}</p>
                <p className="text-xs text-blue-400">Shift Open</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-green-900/30 to-green-800/10 border border-green-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-lg font-bold text-green-300">Rp {((dashboard.sales?.cash || 0) / 1000000).toFixed(1)}jt</p>
                <p className="text-xs text-green-400">Cash Sales</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/10 border border-purple-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <BanknoteIcon className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="text-lg font-bold text-purple-300">Rp {((dashboard.deposits?.total_amount || 0) / 1000000).toFixed(1)}jt</p>
                <p className="text-xs text-purple-400">Deposited</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-red-900/30 to-red-800/10 border border-red-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-lg font-bold text-red-300">{dashboard.discrepancies?.pending_count || 0}</p>
                <p className="text-xs text-red-400">Pending Discrepancy</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        <button
          onClick={() => setActiveTab('shifts')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'shifts' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-shifts"
        >
          <Clock className="h-4 w-4 inline mr-2" />
          Shifts ({shifts.length})
        </button>
        <button
          onClick={() => setActiveTab('discrepancies')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'discrepancies' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-discrepancies"
        >
          <AlertTriangle className="h-4 w-4 inline mr-2" />
          Discrepancies ({discrepancies.length})
        </button>
        <button
          onClick={() => setActiveTab('deposits')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'deposits' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-deposits"
        >
          <Receipt className="h-4 w-4 inline mr-2" />
          Deposits ({deposits.length})
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <input
          type="date"
          value={filterDate}
          onChange={(e) => setFilterDate(e.target.value)}
          className="px-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100"
          data-testid="filter-date"
        />
        
        {activeTab === 'shifts' && (
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100"
            data-testid="filter-status"
          >
            <option value="">Semua Status</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
            <option value="discrepancy">Discrepancy</option>
            <option value="reviewed">Reviewed</option>
          </select>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="h-8 w-8 text-amber-500 animate-spin" />
        </div>
      ) : activeTab === 'shifts' ? (
        <div className="space-y-3">
          {shifts.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Clock className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>Tidak ada shift untuk tanggal ini</p>
            </div>
          ) : (
            shifts.map((shift) => (
              <div 
                key={shift.id}
                className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 hover:border-amber-500/30"
                data-testid={`shift-${shift.id}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <User className="h-8 w-8 text-gray-400" />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-amber-100 font-semibold">{shift.shift_no}</span>
                        <StatusBadge status={shift.status} />
                        {shift.discrepancy_type && shift.discrepancy_type !== 'none' && (
                          <DiscrepancyBadge type={shift.discrepancy_type} />
                        )}
                      </div>
                      <p className="text-gray-400 text-sm">{shift.cashier_name}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-6 text-sm text-right">
                    <div>
                      <span className="text-gray-500 block">Start</span>
                      <span className="text-gray-300">{new Date(shift.start_time).toLocaleTimeString('id-ID')}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block">Initial</span>
                      <span className="text-gray-300">Rp {shift.initial_cash?.toLocaleString('id-ID')}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block">Sales</span>
                      <span className="text-green-400">Rp {shift.sales_summary?.total_sales?.toLocaleString('id-ID') || '0'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block">Discrepancy</span>
                      <span className={shift.discrepancy < 0 ? 'text-red-400' : shift.discrepancy > 0 ? 'text-blue-400' : 'text-gray-400'}>
                        {shift.discrepancy !== undefined ? `Rp ${shift.discrepancy?.toLocaleString('id-ID')}` : '-'}
                      </span>
                    </div>
                  </div>
                  
                  {shift.status === 'open' && shift.cashier_id === currentShift?.cashier_id && (
                    <button
                      onClick={() => setShiftToClose(shift)}
                      className="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white text-sm rounded-lg"
                    >
                      Tutup
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      ) : activeTab === 'discrepancies' ? (
        <div className="space-y-3">
          {discrepancies.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <CheckCircle2 className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>Tidak ada discrepancy pending</p>
            </div>
          ) : (
            discrepancies.map((disc) => (
              <div 
                key={disc.id}
                className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4"
                data-testid={`discrepancy-${disc.id}`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-amber-100 font-semibold">{disc.shift_no}</span>
                      <DiscrepancyBadge type={disc.discrepancy_type} />
                      <StatusBadge status={disc.status} />
                    </div>
                    <p className="text-gray-400 text-sm">{disc.cashier_name}</p>
                  </div>
                  
                  <div className="text-right">
                    <p className="text-gray-500 text-sm">Amount</p>
                    <p className={`text-lg font-bold ${disc.discrepancy_type === 'shortage' ? 'text-red-400' : 'text-blue-400'}`}>
                      Rp {disc.discrepancy_amount?.toLocaleString('id-ID')}
                    </p>
                  </div>
                  
                  {disc.status === 'pending' && (
                    <button
                      onClick={() => handleResolveDiscrepancy(disc.id)}
                      className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white text-sm rounded-lg"
                    >
                      Resolve
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {deposits.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Receipt className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>Tidak ada deposit untuk tanggal ini</p>
            </div>
          ) : (
            deposits.map((dep) => (
              <div 
                key={dep.id}
                className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4"
                data-testid={`deposit-${dep.id}`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-amber-100 font-semibold">{dep.deposit_no}</span>
                    <p className="text-gray-400 text-sm">{dep.cashier_name} - {dep.shift_no}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-green-400 font-bold">Rp {dep.deposit_amount?.toLocaleString('id-ID')}</p>
                    <p className="text-gray-500 text-xs">{dep.deposit_method}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Modals */}
      {showOpenShift && (
        <OpenShiftModal
          onClose={() => setShowOpenShift(false)}
          onSave={() => {
            setShowOpenShift(false);
            fetchData();
          }}
          token={token}
          branches={branches}
        />
      )}
      
      {shiftToClose && (
        <CloseShiftModal
          shift={shiftToClose}
          onClose={() => setShiftToClose(null)}
          onSave={() => {
            setShiftToClose(null);
            fetchData();
          }}
          token={token}
        />
      )}
    </div>
  );
};

export default CashControl;
