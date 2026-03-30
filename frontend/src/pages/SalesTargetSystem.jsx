import React, { useState, useEffect, useCallback } from 'react';
import { 
  Target, TrendingUp, Users, Building2, RefreshCw, Plus,
  Calendar, DollarSign, Award, AlertTriangle, CheckCircle2,
  ChevronUp, ChevronDown, Edit, Trash2, X
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

import { getApiUrl } from '../utils/apiConfig';
const API_URL = getApiUrl();

// Status Badge
const StatusBadge = ({ status }) => {
  const styles = {
    on_track: 'bg-green-500/20 text-green-300 border-green-500/30',
    behind: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    at_risk: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    achieved: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    exceeded: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    failed: 'bg-red-500/20 text-red-300 border-red-500/30'
  };
  
  const labels = {
    on_track: 'On Track',
    behind: 'Behind',
    at_risk: 'At Risk',
    achieved: 'Achieved',
    exceeded: 'Exceeded',
    failed: 'Failed'
  };
  
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded border ${styles[status] || styles.on_track}`}>
      {labels[status] || status}
    </span>
  );
};

// Progress Bar
const ProgressBar = ({ value, max, color = 'amber' }) => {
  const percent = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  
  const colors = {
    amber: 'bg-amber-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
    blue: 'bg-blue-500'
  };
  
  return (
    <div className="h-2 bg-black/30 rounded-full overflow-hidden">
      <div 
        className={`h-full ${colors[color]} transition-all`}
        style={{ width: `${percent}%` }}
      />
    </div>
  );
};

// Create Target Modal
const CreateTargetModal = ({ onClose, onSave, token }) => {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    target_type: 'branch',
    target_ref_id: '',
    target_ref_name: '',
    period_type: 'monthly',
    period_start: new Date().toISOString().slice(0, 10),
    period_end: '',
    target_value: 0,
    notes: ''
  });
  const [branches, setBranches] = useState([]);
  const [users, setUsers] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [branchRes, userRes] = await Promise.all([
          fetch(`${API_URL}/api/branches`, { headers: { 'Authorization': `Bearer ${token}` }}),
          fetch(`${API_URL}/api/users`, { headers: { 'Authorization': `Bearer ${token}` }})
        ]);
        
        const [branchData, userData] = await Promise.all([
          branchRes.json(),
          userRes.json()
        ]);
        
        setBranches(branchData.items || branchData || []);
        setUsers(userData.items || userData || []);
      } catch (err) {
        console.error('Error:', err);
      }
    };
    fetchData();
  }, [token]);

  // Auto calculate period end
  useEffect(() => {
    if (form.period_start && form.period_type) {
      const start = new Date(form.period_start);
      let end;
      
      switch (form.period_type) {
        case 'daily':
          end = start;
          break;
        case 'weekly':
          end = new Date(start);
          end.setDate(end.getDate() + 6);
          break;
        case 'monthly':
          end = new Date(start.getFullYear(), start.getMonth() + 1, 0);
          break;
        case 'quarterly':
          end = new Date(start);
          end.setMonth(end.getMonth() + 3);
          end.setDate(0);
          break;
        case 'yearly':
          end = new Date(start.getFullYear(), 11, 31);
          break;
        default:
          end = start;
      }
      
      setForm({...form, period_end: end.toISOString().slice(0, 10)});
    }
  }, [form.period_start, form.period_type]);

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/sales-target`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(form)
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Gagal membuat target');
      }
      
      onSave();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefSelect = (refId, refName) => {
    setForm({...form, target_ref_id: refId, target_ref_name: refName});
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl max-w-md w-full">
        <div className="p-6 border-b border-red-900/30 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-amber-100">Tambah Target</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Tipe Target</label>
            <select
              value={form.target_type}
              onChange={(e) => setForm({...form, target_type: e.target.value, target_ref_id: '', target_ref_name: ''})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              data-testid="target-type-select"
            >
              <option value="branch">Per Cabang</option>
              <option value="salesman">Per Salesman</option>
              <option value="category">Per Kategori</option>
            </select>
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">
              {form.target_type === 'branch' ? 'Cabang' : form.target_type === 'salesman' ? 'Salesman' : 'Kategori'}
            </label>
            <select
              value={form.target_ref_id}
              onChange={(e) => {
                const selected = form.target_type === 'branch' 
                  ? branches.find(b => b.id === e.target.value)
                  : users.find(u => u.id === e.target.value);
                handleRefSelect(e.target.value, selected?.name || '');
              }}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              data-testid="target-ref-select"
            >
              <option value="">Pilih...</option>
              {form.target_type === 'branch' && branches.map(b => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
              {form.target_type === 'salesman' && users.filter(u => u.role === 'sales' || u.role === 'kasir').map(u => (
                <option key={u.id} value={u.id}>{u.name}</option>
              ))}
            </select>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Periode</label>
              <select
                value={form.period_type}
                onChange={(e) => setForm({...form, period_type: e.target.value})}
                className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
                data-testid="period-type-select"
              >
                <option value="daily">Harian</option>
                <option value="weekly">Mingguan</option>
                <option value="monthly">Bulanan</option>
                <option value="quarterly">Kuartalan</option>
                <option value="yearly">Tahunan</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Mulai</label>
              <input
                type="date"
                value={form.period_start}
                onChange={(e) => setForm({...form, period_start: e.target.value})}
                className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
                data-testid="period-start-input"
              />
            </div>
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Target Nilai (Rp)</label>
            <input
              type="number"
              value={form.target_value}
              onChange={(e) => setForm({...form, target_value: parseFloat(e.target.value) || 0})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              placeholder="0"
              data-testid="target-value-input"
            />
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Catatan</label>
            <input
              type="text"
              value={form.notes}
              onChange={(e) => setForm({...form, notes: e.target.value})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              placeholder="Catatan target..."
            />
          </div>
        </div>
        
        <div className="p-6 border-t border-red-900/30 flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-amber-100">
            Batal
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !form.target_ref_id || form.target_value <= 0}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg disabled:opacity-50"
            data-testid="save-target-btn"
          >
            {loading ? 'Menyimpan...' : 'Simpan'}
          </button>
        </div>
      </div>
    </div>
  );
};

const SalesTargetSystem = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  
  // Data states
  const [targets, setTargets] = useState([]);
  const [summary, setSummary] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  
  // Filter states
  const [filterType, setFilterType] = useState('');
  const [filterPeriod, setFilterPeriod] = useState('monthly');
  const [filterStatus, setFilterStatus] = useState('');
  
  // Modal
  const [showCreate, setShowCreate] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (filterType) params.append('target_type', filterType);
      if (filterPeriod) params.append('period_type', filterPeriod);
      if (filterStatus) params.append('status', filterStatus);
      
      const [listRes, dashRes, leaderRes] = await Promise.all([
        fetch(`${API_URL}/api/sales-target/list?${params}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/sales-target/dashboard/summary?period_type=${filterPeriod}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/sales-target/leaderboard?period_type=${filterPeriod}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      
      const [listData, dashData, leaderData] = await Promise.all([
        listRes.json(),
        dashRes.json(),
        leaderRes.json()
      ]);
      
      setTargets(listData.items || []);
      setSummary(listData.summary || null);
      setDashboard(dashData);
      setLeaderboard(leaderData.items || []);
      
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, filterType, filterPeriod, filterStatus]);

  useEffect(() => {
    if (token) fetchData();
  }, [token, fetchData]);

  const handleDelete = async (targetId) => {
    if (!confirm('Hapus target ini?')) return;
    
    try {
      await fetch(`${API_URL}/api/sales-target/${targetId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchData();
    } catch (err) {
      alert('Gagal menghapus');
    }
  };

  return (
    <div className="space-y-6" data-testid="sales-target-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Sales Target</h1>
          <p className="text-gray-400 text-sm mt-1">Kelola target dan pantau pencapaian</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg"
            data-testid="add-target-btn"
          >
            <Plus className="h-4 w-4" />
            Tambah Target
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

      {/* Overall Summary */}
      {dashboard && (
        <div className="bg-gradient-to-br from-amber-900/30 to-amber-800/10 border border-amber-700/30 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-amber-100">Overall Achievement</h3>
              <p className="text-sm text-gray-400">{filterPeriod}</p>
            </div>
            <StatusBadge status={dashboard.overall_status} />
          </div>
          
          <div className="grid grid-cols-3 gap-6 mb-4">
            <div>
              <p className="text-sm text-gray-400">Target</p>
              <p className="text-xl font-bold text-amber-100">
                Rp {(dashboard.total_target || 0).toLocaleString('id-ID')}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-400">Actual</p>
              <p className="text-xl font-bold text-green-400">
                Rp {(dashboard.total_actual || 0).toLocaleString('id-ID')}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-400">Achievement</p>
              <p className="text-xl font-bold text-amber-100">
                {dashboard.overall_achievement || 0}%
              </p>
            </div>
          </div>
          
          <ProgressBar 
            value={dashboard.total_actual || 0} 
            max={dashboard.total_target || 1}
            color={dashboard.overall_achievement >= 100 ? 'green' : dashboard.overall_achievement >= 80 ? 'amber' : 'red'}
          />
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-gradient-to-br from-green-900/30 to-green-800/10 border border-green-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-8 w-8 text-green-400" />
              <div>
                <p className="text-2xl font-bold text-green-300">{summary.achieved || 0}</p>
                <p className="text-xs text-green-400">Achieved</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/10 border border-blue-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-8 w-8 text-blue-400" />
              <div>
                <p className="text-2xl font-bold text-blue-300">{summary.on_track || 0}</p>
                <p className="text-xs text-blue-400">On Track</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-yellow-900/30 to-yellow-800/10 border border-yellow-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-8 w-8 text-yellow-400" />
              <div>
                <p className="text-2xl font-bold text-yellow-300">{summary.behind || 0}</p>
                <p className="text-xs text-yellow-400">Behind</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-red-900/30 to-red-800/10 border border-red-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <Target className="h-8 w-8 text-red-400" />
              <div>
                <p className="text-2xl font-bold text-red-300">{summary.failed || 0}</p>
                <p className="text-xs text-red-400">Failed</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/10 border border-purple-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <DollarSign className="h-8 w-8 text-purple-400" />
              <div>
                <p className="text-lg font-bold text-purple-300">
                  Rp {((summary.total_actual || 0) / 1000000).toFixed(1)}jt
                </p>
                <p className="text-xs text-purple-400">Total Actual</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'all' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-all"
        >
          <Target className="h-4 w-4 inline mr-2" />
          Semua Target
        </button>
        <button
          onClick={() => setActiveTab('leaderboard')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'leaderboard' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-leaderboard"
        >
          <Award className="h-4 w-4 inline mr-2" />
          Leaderboard
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
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
        
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100"
          data-testid="filter-type"
        >
          <option value="">Semua Tipe</option>
          <option value="branch">Per Cabang</option>
          <option value="salesman">Per Salesman</option>
        </select>
        
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100"
          data-testid="filter-status"
        >
          <option value="">Semua Status</option>
          <option value="on_track">On Track</option>
          <option value="behind">Behind</option>
          <option value="achieved">Achieved</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="h-8 w-8 text-amber-500 animate-spin" />
        </div>
      ) : activeTab === 'all' ? (
        <div className="space-y-3">
          {targets.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Target className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>Belum ada target</p>
              <button
                onClick={() => setShowCreate(true)}
                className="mt-4 text-amber-400 hover:text-amber-300"
              >
                + Tambah Target Pertama
              </button>
            </div>
          ) : (
            targets.map((target) => (
              <div 
                key={target.id}
                className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 hover:border-amber-500/30"
                data-testid={`target-${target.id}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      {target.target_type === 'branch' ? (
                        <Building2 className="h-5 w-5 text-blue-400" />
                      ) : (
                        <Users className="h-5 w-5 text-green-400" />
                      )}
                      <span className="text-amber-100 font-semibold">{target.target_ref_name}</span>
                      <span className="text-gray-500 text-sm">{target.period_type}</span>
                      <StatusBadge status={target.status} />
                    </div>
                    
                    <div className="grid grid-cols-5 gap-4 text-sm mb-3">
                      <div>
                        <span className="text-gray-500">Periode</span>
                        <p className="text-gray-300">{target.period_start} - {target.period_end}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Target</span>
                        <p className="text-amber-100">Rp {target.target_value?.toLocaleString('id-ID')}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Actual</span>
                        <p className="text-green-400">Rp {target.actual_value?.toLocaleString('id-ID')}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Achievement</span>
                        <p className={`font-bold ${target.achievement_percent >= 100 ? 'text-green-400' : target.achievement_percent >= 80 ? 'text-amber-100' : 'text-red-400'}`}>
                          {target.achievement_percent}%
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-500">Gap</span>
                        <p className={target.gap > 0 ? 'text-red-400' : 'text-green-400'}>
                          {target.gap > 0 ? '-' : '+'}Rp {Math.abs(target.gap)?.toLocaleString('id-ID')}
                        </p>
                      </div>
                    </div>
                    
                    <ProgressBar 
                      value={target.actual_value || 0} 
                      max={target.target_value || 1}
                      color={target.achievement_percent >= 100 ? 'green' : target.achievement_percent >= 80 ? 'amber' : 'red'}
                    />
                  </div>
                  
                  <button
                    onClick={() => handleDelete(target.id)}
                    className="p-2 text-red-400 hover:text-red-300 ml-4"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-black/30">
              <tr className="text-left text-sm text-gray-400">
                <th className="p-4 w-16">Rank</th>
                <th className="p-4">Salesman</th>
                <th className="p-4 text-right">Target</th>
                <th className="p-4 text-right">Actual</th>
                <th className="p-4 text-right">Achievement</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((item, idx) => (
                <tr 
                  key={item.salesman_id}
                  className="border-t border-red-900/20 hover:bg-red-900/10"
                >
                  <td className="p-4">
                    <span className={`h-8 w-8 rounded-full flex items-center justify-center font-bold ${
                      idx === 0 ? 'bg-amber-500/30 text-amber-300' :
                      idx === 1 ? 'bg-gray-400/30 text-gray-300' :
                      idx === 2 ? 'bg-orange-500/30 text-orange-300' :
                      'bg-black/30 text-gray-400'
                    }`}>
                      {item.rank}
                    </span>
                  </td>
                  <td className="p-4 text-amber-100 font-medium">{item.salesman_name}</td>
                  <td className="p-4 text-right text-gray-300">
                    Rp {item.target_value?.toLocaleString('id-ID')}
                  </td>
                  <td className="p-4 text-right text-green-400">
                    Rp {item.actual_value?.toLocaleString('id-ID')}
                  </td>
                  <td className="p-4 text-right">
                    <span className={`font-bold ${
                      item.achievement_percent >= 100 ? 'text-green-400' : 
                      item.achievement_percent >= 80 ? 'text-amber-100' : 'text-red-400'
                    }`}>
                      {item.achievement_percent}%
                    </span>
                  </td>
                  <td className="p-4">
                    <StatusBadge status={item.status} />
                  </td>
                </tr>
              ))}
              {leaderboard.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-gray-500">
                    Tidak ada data leaderboard
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <CreateTargetModal
          onClose={() => setShowCreate(false)}
          onSave={() => {
            setShowCreate(false);
            fetchData();
          }}
          token={token}
        />
      )}
    </div>
  );
};

export default SalesTargetSystem;
