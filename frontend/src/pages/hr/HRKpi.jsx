// OCB TITAN ERP - HR KPI Engine UI
// TASK 3: KPI Dashboard for Performance Management

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Target, Trophy, TrendingUp, Users, Plus, Search, Filter, 
  CheckCircle, AlertCircle, Clock, Star, Award, BarChart3,
  Edit, Eye, RefreshCw, Loader2, ChevronDown, ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';

// Design constants
const DESIGN = {
  bg: { primary: 'bg-[#0a0608]', secondary: 'bg-[#1a1214]', card: 'bg-[#1a1214]' },
  border: { default: 'border-red-900/30', accent: 'border-amber-600/30' },
  text: { primary: 'text-gray-200', secondary: 'text-gray-400', accent: 'text-amber-400' }
};

// Rating configurations
const RATING_CONFIG = {
  exceeds: { label: 'Melebihi Target', bg: 'bg-green-500/20', text: 'text-green-400', icon: Trophy },
  meets: { label: 'Memenuhi Target', bg: 'bg-blue-500/20', text: 'text-blue-400', icon: CheckCircle },
  below: { label: 'Di Bawah Target', bg: 'bg-amber-500/20', text: 'text-amber-400', icon: AlertCircle },
  unsatisfactory: { label: 'Tidak Memuaskan', bg: 'bg-red-500/20', text: 'text-red-400', icon: AlertCircle },
  pending: { label: 'Pending', bg: 'bg-gray-500/20', text: 'text-gray-400', icon: Clock }
};

const CATEGORY_CONFIG = {
  performance: { label: 'Performa', bg: 'bg-blue-500/20', text: 'text-blue-400' },
  sales: { label: 'Penjualan', bg: 'bg-green-500/20', text: 'text-green-400' },
  quality: { label: 'Kualitas', bg: 'bg-purple-500/20', text: 'text-purple-400' },
  attendance: { label: 'Kehadiran', bg: 'bg-amber-500/20', text: 'text-amber-400' }
};

// Stat Card Component
const StatCard = ({ icon: Icon, label, value, subValue, color = 'amber' }) => (
  <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl p-4`} data-testid={`stat-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-center gap-3 mb-2">
      <div className={`p-2 rounded-lg bg-${color}-500/20`}>
        <Icon className={`h-5 w-5 text-${color}-400`} />
      </div>
      <span className="text-gray-400 text-sm">{label}</span>
    </div>
    <p className={`text-2xl font-bold text-${color}-400`}>{value}</p>
    {subValue && <p className="text-xs text-gray-500 mt-1">{subValue}</p>}
  </div>
);

// Rating Badge Component
const RatingBadge = ({ rating }) => {
  const config = RATING_CONFIG[rating] || RATING_CONFIG.pending;
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${config.bg} ${config.text}`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  );
};

// Category Badge Component  
const CategoryBadge = ({ category }) => {
  const config = CATEGORY_CONFIG[category] || CATEGORY_CONFIG.performance;
  return (
    <span className={`px-2 py-1 rounded-full text-xs ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
};

// Achievement Progress Bar
const AchievementBar = ({ achievement }) => {
  const pct = Math.min(achievement * 100, 150);
  const color = achievement >= 1 ? 'bg-green-500' : achievement >= 0.7 ? 'bg-amber-500' : 'bg-red-500';
  
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">Achievement</span>
        <span className={achievement >= 1 ? 'text-green-400' : 'text-gray-300'}>{(achievement * 100).toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all duration-500`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
    </div>
  );
};

// KPI Target Modal
const KPITargetModal = ({ isOpen, onClose, onSave, editData }) => {
  const [formData, setFormData] = useState({
    name: '', code: '', description: '', category: 'performance',
    metric_type: 'number', target_value: '', weight: '1', period_type: 'monthly'
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (editData) {
      setFormData({
        name: editData.name || '',
        code: editData.code || '',
        description: editData.description || '',
        category: editData.category || 'performance',
        metric_type: editData.metric_type || 'number',
        target_value: editData.target_value?.toString() || '',
        weight: editData.weight?.toString() || '1',
        period_type: editData.period_type || 'monthly'
      });
    } else {
      setFormData({ name: '', code: '', description: '', category: 'performance', metric_type: 'number', target_value: '', weight: '1', period_type: 'monthly' });
    }
  }, [editData, isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.code || !formData.target_value) {
      toast.error('Lengkapi data wajib');
      return;
    }
    setLoading(true);
    await onSave({
      ...formData,
      target_value: parseFloat(formData.target_value),
      weight: parseFloat(formData.weight)
    });
    setLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onClose}>
      <div className={`${DESIGN.bg.secondary} border ${DESIGN.border.default} rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto`} onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-amber-100 mb-4 flex items-center gap-2">
          <Target className="h-5 w-5 text-amber-400" />
          {editData ? 'Edit KPI Target' : 'Tambah KPI Target'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Kode KPI *</label>
              <input type="text" value={formData.code} onChange={e => setFormData({...formData, code: e.target.value.toUpperCase()})}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
                placeholder="SALES-001" data-testid="kpi-code-input" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Kategori</label>
              <select value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" data-testid="kpi-category-select">
                <option value="performance">Performa</option>
                <option value="sales">Penjualan</option>
                <option value="quality">Kualitas</option>
                <option value="attendance">Kehadiran</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Nama KPI *</label>
            <input type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
              placeholder="Total Penjualan Bulanan" data-testid="kpi-name-input" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Deskripsi</label>
            <textarea value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
              rows={2} placeholder="Deskripsi KPI..." />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Target *</label>
              <input type="number" value={formData.target_value} onChange={e => setFormData({...formData, target_value: e.target.value})}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
                placeholder="100" data-testid="kpi-target-input" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Bobot</label>
              <input type="number" step="0.1" value={formData.weight} onChange={e => setFormData({...formData, weight: e.target.value})}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
                placeholder="1.0" data-testid="kpi-weight-input" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Periode</label>
              <select value={formData.period_type} onChange={e => setFormData({...formData, period_type: e.target.value})}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200">
                <option value="monthly">Bulanan</option>
                <option value="quarterly">Kuartalan</option>
                <option value="yearly">Tahunan</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 bg-gray-600/20 text-gray-300 rounded-lg hover:bg-gray-600/30">
              Batal
            </button>
            <button type="submit" disabled={loading} className="flex-1 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 flex items-center justify-center gap-2" data-testid="save-kpi-target-btn">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
              Simpan
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Assign KPI Modal
const AssignKPIModal = ({ isOpen, onClose, onSave, targets, employees }) => {
  const [formData, setFormData] = useState({ employee_id: '', kpi_target_id: '', period: '', target_value: '', notes: '' });
  const [loading, setLoading] = useState(false);

  const currentMonth = new Date().toISOString().slice(0, 7);

  useEffect(() => {
    if (isOpen) {
      setFormData({ employee_id: '', kpi_target_id: '', period: currentMonth, target_value: '', notes: '' });
    }
  }, [isOpen, currentMonth]);

  const handleTargetSelect = (targetId) => {
    const target = targets.find(t => t.id === targetId);
    setFormData({
      ...formData, 
      kpi_target_id: targetId,
      target_value: target?.target_value?.toString() || ''
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.employee_id || !formData.kpi_target_id || !formData.period) {
      toast.error('Lengkapi data wajib');
      return;
    }
    setLoading(true);
    await onSave({
      ...formData,
      target_value: formData.target_value ? parseFloat(formData.target_value) : null
    });
    setLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onClose}>
      <div className={`${DESIGN.bg.secondary} border ${DESIGN.border.default} rounded-xl p-6 w-full max-w-lg`} onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-amber-100 mb-4 flex items-center gap-2">
          <Users className="h-5 w-5 text-amber-400" />
          Assign KPI ke Karyawan
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Karyawan *</label>
            <select value={formData.employee_id} onChange={e => setFormData({...formData, employee_id: e.target.value})}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" data-testid="assign-employee-select">
              <option value="">Pilih Karyawan</option>
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.employee_id || emp.id} - {emp.full_name || emp.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">KPI Target *</label>
            <select value={formData.kpi_target_id} onChange={e => handleTargetSelect(e.target.value)}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" data-testid="assign-kpi-select">
              <option value="">Pilih KPI</option>
              {targets.map(t => (
                <option key={t.id} value={t.id}>{t.code} - {t.name} (Target: {t.target_value})</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Periode *</label>
              <input type="month" value={formData.period} onChange={e => setFormData({...formData, period: e.target.value})}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" data-testid="assign-period-input" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Target Override</label>
              <input type="number" value={formData.target_value} onChange={e => setFormData({...formData, target_value: e.target.value})}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
                placeholder="Kosongkan untuk default" />
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Catatan</label>
            <textarea value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
              rows={2} placeholder="Catatan assignment..." />
          </div>
          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 bg-gray-600/20 text-gray-300 rounded-lg">Batal</button>
            <button type="submit" disabled={loading} className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg flex items-center justify-center gap-2" data-testid="confirm-assign-btn">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Assign
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Update Result Modal
const UpdateResultModal = ({ isOpen, onClose, onSave, result }) => {
  const [formData, setFormData] = useState({ actual_value: '', notes: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (result && isOpen) {
      setFormData({ actual_value: result.actual_value?.toString() || '', notes: result.notes || '' });
    }
  }, [result, isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.actual_value) {
      toast.error('Masukkan nilai aktual');
      return;
    }
    setLoading(true);
    await onSave(result.id, { actual_value: parseFloat(formData.actual_value), notes: formData.notes });
    setLoading(false);
  };

  if (!isOpen || !result) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onClose}>
      <div className={`${DESIGN.bg.secondary} border ${DESIGN.border.default} rounded-xl p-6 w-full max-w-md`} onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-amber-100 mb-4 flex items-center gap-2">
          <Edit className="h-5 w-5 text-amber-400" />
          Update Pencapaian KPI
        </h2>
        <div className="mb-4 p-3 bg-[#0a0608] rounded-lg">
          <p className="text-gray-400 text-sm">{result.kpi_name}</p>
          <p className="text-amber-200 font-medium">{result.employee_name}</p>
          <p className="text-gray-500 text-xs">Target: {result.target_value} | Periode: {result.period}</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Nilai Aktual *</label>
            <input type="number" step="0.01" value={formData.actual_value} onChange={e => setFormData({...formData, actual_value: e.target.value})}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
              placeholder="Masukkan pencapaian" data-testid="actual-value-input" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Catatan</label>
            <textarea value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
              rows={2} placeholder="Catatan pencapaian..." />
          </div>
          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 bg-gray-600/20 text-gray-300 rounded-lg">Batal</button>
            <button type="submit" disabled={loading} className="flex-1 px-4 py-2 bg-amber-600 text-white rounded-lg flex items-center justify-center gap-2" data-testid="save-result-btn">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
              Simpan
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main Component
const HRKpi = () => {
  const { api } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [targets, setTargets] = useState([]);
  const [results, setResults] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [summary, setSummary] = useState({ total_weighted_score: 0, average_achievement: 0 });
  
  // Filters
  const [periodFilter, setPeriodFilter] = useState(new Date().toISOString().slice(0, 7));
  const [categoryFilter, setCategoryFilter] = useState('');
  
  // Modals
  const [showTargetModal, setShowTargetModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [selectedResult, setSelectedResult] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Load KPI Targets
      const targetsRes = await api('/api/hr/kpi/targets');
      if (targetsRes.ok) {
        const data = await targetsRes.json();
        setTargets(data.targets || []);
      }
      
      // Load KPI Results
      const params = new URLSearchParams();
      if (periodFilter) params.append('period', periodFilter);
      const resultsRes = await api(`/api/hr/kpi/results?${params}`);
      if (resultsRes.ok) {
        const data = await resultsRes.json();
        setResults(data.results || []);
        setSummary(data.summary || { total_weighted_score: 0, average_achievement: 0 });
      }
      
      // Load Employees
      const empRes = await api('/api/hr/employees?status=active&limit=200');
      if (empRes.ok) {
        const data = await empRes.json();
        setEmployees(data.items || data.employees || []);
      }
    } catch (err) {
      console.error('Load KPI data error:', err);
      toast.error('Gagal memuat data KPI');
    } finally {
      setLoading(false);
    }
  }, [api, periodFilter]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSaveTarget = async (data) => {
    try {
      const res = await api('/api/hr/kpi/targets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        toast.success('KPI Target berhasil dibuat');
        setShowTargetModal(false);
        loadData();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal membuat KPI Target');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const handleAssignKPI = async (data) => {
    try {
      const res = await api('/api/hr/kpi/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        toast.success('KPI berhasil di-assign');
        setShowAssignModal(false);
        loadData();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal assign KPI');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const handleUpdateResult = async (resultId, data) => {
    try {
      const res = await api(`/api/hr/kpi/results/${resultId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        const result = await res.json();
        toast.success(`Achievement: ${result.achievement}% - ${result.rating}`);
        setShowUpdateModal(false);
        loadData();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal update KPI');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  // Stats
  const totalKPIs = results.length;
  const completedKPIs = results.filter(r => r.status === 'reviewed').length;
  const avgAchievement = summary.average_achievement || 0;

  return (
    <div className="space-y-4" data-testid="hr-kpi-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
            <Trophy className="h-6 w-6 text-amber-400" />
            KPI Engine
          </h1>
          <p className="text-gray-400 text-sm">Performance Management System</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowTargetModal(true)} className="px-4 py-2 bg-amber-600/20 text-amber-400 rounded-lg flex items-center gap-2 hover:bg-amber-600/30" data-testid="add-target-btn">
            <Target className="h-4 w-4" /> Tambah Target
          </button>
          <button onClick={() => setShowAssignModal(true)} className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg flex items-center gap-2 hover:bg-green-600/30" data-testid="assign-kpi-btn">
            <Plus className="h-4 w-4" /> Assign KPI
          </button>
          <button onClick={loadData} className="px-3 py-2 bg-gray-600/20 text-gray-400 rounded-lg hover:bg-gray-600/30" data-testid="refresh-btn">
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard icon={Target} label="Total KPI" value={targets.length} subValue="Target terdefinisi" color="amber" />
        <StatCard icon={Users} label="KPI Assigned" value={totalKPIs} subValue={`${completedKPIs} reviewed`} color="blue" />
        <StatCard icon={TrendingUp} label="Avg Achievement" value={`${avgAchievement.toFixed(1)}%`} subValue="Pencapaian rata-rata" color="green" />
        <StatCard icon={Award} label="Total Score" value={summary.total_weighted_score.toFixed(2)} subValue="Skor terbobot" color="purple" />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        {[
          { key: 'dashboard', label: 'Dashboard', icon: BarChart3 },
          { key: 'targets', label: 'KPI Targets', icon: Target },
          { key: 'results', label: 'KPI Results', icon: CheckCircle }
        ].map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${activeTab === tab.key ? 'bg-amber-600/20 text-amber-400' : 'text-gray-400 hover:text-gray-200'}`}
            data-testid={`tab-${tab.key}`}>
            <tab.icon className="h-4 w-4" /> {tab.label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl p-4`}>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Periode</label>
            <input type="month" value={periodFilter} onChange={e => setPeriodFilter(e.target.value)}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" data-testid="period-filter" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Kategori</label>
            <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" data-testid="category-filter">
              <option value="">Semua Kategori</option>
              <option value="performance">Performa</option>
              <option value="sales">Penjualan</option>
              <option value="quality">Kualitas</option>
              <option value="attendance">Kehadiran</option>
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={loadData} className="px-4 py-2 bg-amber-600/20 text-amber-400 rounded-lg flex items-center gap-2 hover:bg-amber-600/30">
              <Filter className="h-4 w-4" /> Filter
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl p-8 text-center`}>
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
          <p className="text-gray-400 mt-2">Memuat data KPI...</p>
        </div>
      ) : activeTab === 'targets' ? (
        /* KPI Targets Tab */
        <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="kpi-targets-table">
              <thead className="bg-red-900/20">
                <tr>
                  <th className="px-4 py-3 text-left text-xs text-gray-400">KODE</th>
                  <th className="px-4 py-3 text-left text-xs text-gray-400">NAMA KPI</th>
                  <th className="px-4 py-3 text-left text-xs text-gray-400">KATEGORI</th>
                  <th className="px-4 py-3 text-right text-xs text-gray-400">TARGET</th>
                  <th className="px-4 py-3 text-right text-xs text-gray-400">BOBOT</th>
                  <th className="px-4 py-3 text-center text-xs text-gray-400">PERIODE</th>
                  <th className="px-4 py-3 text-center text-xs text-gray-400">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/20">
                {targets.length === 0 ? (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Belum ada KPI Target</td></tr>
                ) : targets.filter(t => !categoryFilter || t.category === categoryFilter).map(target => (
                  <tr key={target.id} className="hover:bg-red-900/5" data-testid={`target-row-${target.id}`}>
                    <td className="px-4 py-3 font-mono text-amber-300">{target.code}</td>
                    <td className="px-4 py-3 text-gray-200">{target.name}</td>
                    <td className="px-4 py-3"><CategoryBadge category={target.category} /></td>
                    <td className="px-4 py-3 text-right text-blue-400 font-medium">{target.target_value.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right text-gray-300">{target.weight}</td>
                    <td className="px-4 py-3 text-center text-gray-400 text-sm">{target.period_type}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs ${target.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                        {target.is_active ? 'Aktif' : 'Nonaktif'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : activeTab === 'results' ? (
        /* KPI Results Tab */
        <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="kpi-results-table">
              <thead className="bg-red-900/20">
                <tr>
                  <th className="px-4 py-3 text-left text-xs text-gray-400">KARYAWAN</th>
                  <th className="px-4 py-3 text-left text-xs text-gray-400">KPI</th>
                  <th className="px-4 py-3 text-center text-xs text-gray-400">PERIODE</th>
                  <th className="px-4 py-3 text-right text-xs text-gray-400">TARGET</th>
                  <th className="px-4 py-3 text-right text-xs text-gray-400">AKTUAL</th>
                  <th className="px-4 py-3 text-center text-xs text-gray-400">ACHIEVEMENT</th>
                  <th className="px-4 py-3 text-center text-xs text-gray-400">RATING</th>
                  <th className="px-4 py-3 text-center text-xs text-gray-400">AKSI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/20">
                {results.length === 0 ? (
                  <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Belum ada KPI yang di-assign</td></tr>
                ) : results.map(result => (
                  <tr key={result.id} className="hover:bg-red-900/5" data-testid={`result-row-${result.id}`}>
                    <td className="px-4 py-3">
                      <p className="text-gray-200 font-medium">{result.employee_name}</p>
                      <p className="text-gray-500 text-xs">{result.employee_nik}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-amber-300">{result.kpi_name}</p>
                      <p className="text-gray-500 text-xs">{result.kpi_code}</p>
                    </td>
                    <td className="px-4 py-3 text-center text-gray-400">{result.period}</td>
                    <td className="px-4 py-3 text-right text-gray-300">{result.target_value.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right text-blue-400 font-medium">{result.actual_value.toLocaleString()}</td>
                    <td className="px-4 py-3 w-32">
                      <AchievementBar achievement={result.achievement} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <RatingBadge rating={result.rating || 'pending'} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button onClick={() => { setSelectedResult(result); setShowUpdateModal(true); }}
                        className="p-2 hover:bg-amber-600/20 rounded-lg text-amber-400" title="Update" data-testid={`update-btn-${result.id}`}>
                        <Edit className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Dashboard Tab */
        <div className="grid grid-cols-2 gap-4">
          {/* Top Performers */}
          <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl p-4`}>
            <h3 className="text-lg font-semibold text-amber-100 mb-4 flex items-center gap-2">
              <Trophy className="h-5 w-5 text-amber-400" />
              Top Performers
            </h3>
            <div className="space-y-3">
              {results.length === 0 ? (
                <p className="text-gray-400 text-sm">Belum ada data</p>
              ) : [...results].sort((a, b) => b.weighted_score - a.weighted_score).slice(0, 5).map((result, idx) => (
                <div key={result.id} className="flex items-center justify-between p-3 bg-[#0a0608] rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className={`w-8 h-8 flex items-center justify-center rounded-full font-bold ${idx === 0 ? 'bg-amber-500/20 text-amber-400' : idx === 1 ? 'bg-gray-400/20 text-gray-300' : idx === 2 ? 'bg-orange-500/20 text-orange-400' : 'bg-gray-600/20 text-gray-400'}`}>
                      {idx + 1}
                    </span>
                    <div>
                      <p className="text-gray-200 font-medium">{result.employee_name}</p>
                      <p className="text-gray-500 text-xs">{result.kpi_name}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-green-400 font-bold">{(result.achievement * 100).toFixed(1)}%</p>
                    <p className="text-gray-500 text-xs">Score: {result.weighted_score.toFixed(2)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* KPI by Category */}
          <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl p-4`}>
            <h3 className="text-lg font-semibold text-amber-100 mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-amber-400" />
              KPI by Category
            </h3>
            <div className="space-y-3">
              {Object.entries(CATEGORY_CONFIG).map(([key, config]) => {
                const categoryTargets = targets.filter(t => t.category === key);
                const categoryResults = results.filter(r => r.kpi_category === key);
                const avgAch = categoryResults.length > 0 ? categoryResults.reduce((sum, r) => sum + (r.achievement || 0), 0) / categoryResults.length * 100 : 0;
                return (
                  <div key={key} className="p-3 bg-[#0a0608] rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <CategoryBadge category={key} />
                      <span className="text-gray-400 text-sm">{categoryTargets.length} targets</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300">{categoryResults.length} assigned</span>
                      <span className={`font-bold ${avgAch >= 100 ? 'text-green-400' : avgAch >= 70 ? 'text-amber-400' : 'text-red-400'}`}>
                        {avgAch.toFixed(1)}% avg
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <KPITargetModal isOpen={showTargetModal} onClose={() => { setShowTargetModal(false); setEditTarget(null); }} onSave={handleSaveTarget} editData={editTarget} />
      <AssignKPIModal isOpen={showAssignModal} onClose={() => setShowAssignModal(false)} onSave={handleAssignKPI} targets={targets} employees={employees} />
      <UpdateResultModal isOpen={showUpdateModal} onClose={() => { setShowUpdateModal(false); setSelectedResult(null); }} onSave={handleUpdateResult} result={selectedResult} />
    </div>
  );
};

export default HRKpi;
