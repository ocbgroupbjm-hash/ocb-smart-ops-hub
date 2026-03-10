import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Trophy, TrendingUp, TrendingDown, AlertTriangle, Star, Users, Target, Clock, DollarSign, RefreshCw, Download, ChevronRight, Award, Zap, Shield, AlertCircle } from 'lucide-react';

export default function AIPerformance() {
  const [loading, setLoading] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('all');
  const [selectedPeriod, setSelectedPeriod] = useState('1month');
  const [ranking, setRanking] = useState(null);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [employeeAnalysis, setEmployeeAnalysis] = useState(null);

  useEffect(() => {
    loadBranches();
    loadRanking();
  }, []);

  useEffect(() => {
    loadRanking();
  }, [selectedBranch, selectedPeriod]);

  const loadBranches = async () => {
    try {
      const res = await api.get('/api/erp-operations/branches');
      setBranches(res.data.branches || []);
    } catch (err) {
      console.error('Error loading branches:', err);
    }
  };

  const loadRanking = async () => {
    setLoading(true);
    try {
      let url = `/api/ai-employee/analyze-all?period=${selectedPeriod}`;
      if (selectedBranch !== 'all') {
        url += `&branch_id=${selectedBranch}`;
      }
      const res = await api.get(url);
      setRanking(res.data);
      setEmployees(res.data.all_employees || []);
    } catch (err) {
      console.error('Error loading ranking:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadEmployeeAnalysis = async (employeeId) => {
    try {
      const res = await api.get(`/api/ai-employee/analyze/${employeeId}?period=${selectedPeriod}`);
      setEmployeeAnalysis(res.data);
      setSelectedEmployee(employeeId);
    } catch (err) {
      console.error('Error loading analysis:', err);
    }
  };

  const getCategoryStyle = (category) => {
    const styles = {
      'ELITE': { bg: 'bg-gradient-to-r from-yellow-400 to-amber-500', text: 'text-yellow-900', icon: Trophy },
      'SANGAT_BAIK': { bg: 'bg-gradient-to-r from-green-400 to-emerald-500', text: 'text-green-900', icon: Star },
      'BAIK': { bg: 'bg-gradient-to-r from-blue-400 to-cyan-500', text: 'text-blue-900', icon: TrendingUp },
      'NORMAL': { bg: 'bg-gradient-to-r from-gray-400 to-slate-500', text: 'text-gray-900', icon: Target },
      'PERLU_PERHATIAN': { bg: 'bg-gradient-to-r from-orange-400 to-amber-600', text: 'text-orange-900', icon: AlertTriangle },
      'BURUK': { bg: 'bg-gradient-to-r from-red-500 to-rose-600', text: 'text-red-100', icon: AlertCircle }
    };
    return styles[category] || styles['NORMAL'];
  };

  const formatRupiah = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(num);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6" data-testid="ai-performance-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Zap className="w-8 h-8 text-yellow-400" />
            AI Performance Analysis
          </h1>
          <p className="text-slate-400 mt-1">Analisis performa karyawan berbasis AI</p>
        </div>
        
        <div className="flex gap-3 flex-wrap">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-40 bg-slate-800 border-slate-700 text-white" data-testid="period-select">
              <SelectValue placeholder="Periode" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1month">1 Bulan</SelectItem>
              <SelectItem value="3months">3 Bulan</SelectItem>
              <SelectItem value="6months">6 Bulan</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={selectedBranch} onValueChange={setSelectedBranch}>
            <SelectTrigger className="w-48 bg-slate-800 border-slate-700 text-white" data-testid="branch-select">
              <SelectValue placeholder="Semua Cabang" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Semua Cabang</SelectItem>
              {branches.map(b => (
                <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Button onClick={loadRanking} disabled={loading} className="bg-purple-600 hover:bg-purple-700" data-testid="refresh-btn">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Category Summary Cards */}
      {ranking && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          {['ELITE', 'SANGAT_BAIK', 'BAIK', 'NORMAL', 'PERLU_PERHATIAN', 'BURUK'].map(cat => {
            const style = getCategoryStyle(cat);
            const Icon = style.icon;
            const count = ranking.category_summary?.[cat] || 0;
            return (
              <Card key={cat} className={`${style.bg} border-0`} data-testid={`category-card-${cat.toLowerCase()}`}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <Icon className={`w-8 h-8 ${style.text} opacity-80`} />
                    <span className={`text-3xl font-bold ${style.text}`}>{count}</span>
                  </div>
                  <p className={`text-sm mt-2 ${style.text} font-medium`}>
                    {cat.replace('_', ' ')}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Employee List */}
        <div className="lg:col-span-2">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-400" />
                Ranking Karyawan ({employees.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {loading ? (
                  <div className="text-center py-8 text-slate-400">Memuat data...</div>
                ) : employees.length === 0 ? (
                  <div className="text-center py-8 text-slate-400">Tidak ada data karyawan</div>
                ) : (
                  employees.map((emp, idx) => {
                    const style = getCategoryStyle(emp.category);
                    const Icon = style.icon;
                    return (
                      <div
                        key={emp.employee_id}
                        onClick={() => loadEmployeeAnalysis(emp.employee_id)}
                        className={`p-4 rounded-lg cursor-pointer transition-all duration-200 ${
                          selectedEmployee === emp.employee_id 
                            ? 'bg-purple-600/30 border border-purple-500' 
                            : 'bg-slate-700/50 hover:bg-slate-700 border border-transparent'
                        }`}
                        data-testid={`employee-row-${idx}`}
                      >
                        <div className="flex items-center gap-4">
                          {/* Rank Badge */}
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            idx < 3 ? 'bg-yellow-500 text-yellow-900' : 'bg-slate-600 text-slate-300'
                          } font-bold`}>
                            {emp.rank}
                          </div>
                          
                          {/* Employee Info */}
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-white font-medium">{emp.name}</span>
                              <span className={`px-2 py-0.5 rounded-full text-xs ${style.bg} ${style.text}`}>
                                {emp.category.replace('_', ' ')}
                              </span>
                            </div>
                            <div className="text-sm text-slate-400">
                              {emp.jabatan} - {emp.branch}
                            </div>
                          </div>
                          
                          {/* Score */}
                          <div className="text-right">
                            <div className="text-2xl font-bold text-white">{emp.score}</div>
                            <div className="text-xs text-slate-400">Score</div>
                          </div>
                          
                          {/* Stats */}
                          <div className="hidden md:flex gap-4 text-sm">
                            <div className="text-center">
                              <div className="text-green-400 font-medium">{emp.strengths_count}</div>
                              <div className="text-slate-500 text-xs">Kelebihan</div>
                            </div>
                            <div className="text-center">
                              <div className="text-red-400 font-medium">{emp.weaknesses_count}</div>
                              <div className="text-slate-500 text-xs">Kelemahan</div>
                            </div>
                          </div>
                          
                          <ChevronRight className="w-5 h-5 text-slate-500" />
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detail Panel */}
        <div>
          {employeeAnalysis ? (
            <Card className="bg-slate-800/50 border-slate-700 sticky top-6">
              <CardHeader className={`${getCategoryStyle(employeeAnalysis.category).bg} rounded-t-lg`}>
                <CardTitle className={`${getCategoryStyle(employeeAnalysis.category).text} flex items-center gap-2`}>
                  {React.createElement(getCategoryStyle(employeeAnalysis.category).icon, { className: 'w-6 h-6' })}
                  {employeeAnalysis.employee.name}
                </CardTitle>
                <p className={`text-sm ${getCategoryStyle(employeeAnalysis.category).text} opacity-80`}>
                  {employeeAnalysis.employee.jabatan} - {employeeAnalysis.employee.branch}
                </p>
              </CardHeader>
              <CardContent className="p-4 space-y-4">
                {/* Score */}
                <div className="text-center py-4 bg-slate-700/50 rounded-lg">
                  <div className="text-5xl font-bold text-white">{employeeAnalysis.score}</div>
                  <div className="text-slate-400 mt-1">Performance Score</div>
                  <div className={`inline-block mt-2 px-3 py-1 rounded-full text-sm ${getCategoryStyle(employeeAnalysis.category).bg} ${getCategoryStyle(employeeAnalysis.category).text}`}>
                    {employeeAnalysis.category_description}
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-700/50 p-3 rounded-lg">
                    <Clock className="w-5 h-5 text-blue-400 mb-1" />
                    <div className="text-lg font-bold text-white">{employeeAnalysis.metrics.attendance.total_hadir}</div>
                    <div className="text-xs text-slate-400">Hari Hadir</div>
                  </div>
                  <div className="bg-slate-700/50 p-3 rounded-lg">
                    <AlertTriangle className="w-5 h-5 text-red-400 mb-1" />
                    <div className="text-lg font-bold text-white">{employeeAnalysis.metrics.attendance.total_alpha}</div>
                    <div className="text-xs text-slate-400">Hari Alpha</div>
                  </div>
                  <div className="bg-slate-700/50 p-3 rounded-lg">
                    <DollarSign className="w-5 h-5 text-green-400 mb-1" />
                    <div className="text-lg font-bold text-white">{formatRupiah(employeeAnalysis.metrics.sales.total_sales)}</div>
                    <div className="text-xs text-slate-400">Total Sales</div>
                  </div>
                  <div className="bg-slate-700/50 p-3 rounded-lg">
                    <Target className="w-5 h-5 text-purple-400 mb-1" />
                    <div className="text-lg font-bold text-white">{employeeAnalysis.metrics.sales.total_transactions}</div>
                    <div className="text-xs text-slate-400">Transaksi</div>
                  </div>
                </div>

                {/* Strengths */}
                {employeeAnalysis.strengths.length > 0 && (
                  <div>
                    <h4 className="text-green-400 font-medium mb-2 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" /> Kelebihan
                    </h4>
                    <ul className="space-y-1">
                      {employeeAnalysis.strengths.map((s, i) => (
                        <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                          <span className="text-green-400">✓</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Weaknesses */}
                {employeeAnalysis.weaknesses.length > 0 && (
                  <div>
                    <h4 className="text-red-400 font-medium mb-2 flex items-center gap-2">
                      <TrendingDown className="w-4 h-4" /> Kelemahan
                    </h4>
                    <ul className="space-y-1">
                      {employeeAnalysis.weaknesses.map((w, i) => (
                        <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                          <span className="text-red-400">!</span> {w}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Recommendations */}
                {employeeAnalysis.recommendations.length > 0 && (
                  <div className="bg-purple-900/30 p-3 rounded-lg border border-purple-500/30">
                    <h4 className="text-purple-400 font-medium mb-2 flex items-center gap-2">
                      <Award className="w-4 h-4" /> Rekomendasi AI
                    </h4>
                    <ul className="space-y-1">
                      {employeeAnalysis.recommendations.map((r, i) => (
                        <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                          <span className="text-purple-400">→</span> {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Minus Kas Warning */}
                {employeeAnalysis.metrics.minus_kas.total > 0 && (
                  <div className="bg-red-900/30 p-3 rounded-lg border border-red-500/30">
                    <div className="flex items-center gap-2 text-red-400">
                      <Shield className="w-5 h-5" />
                      <span className="font-medium">Peringatan Minus Kas</span>
                    </div>
                    <p className="text-sm text-slate-300 mt-1">
                      Total minus kas: {formatRupiah(employeeAnalysis.metrics.minus_kas.total)} ({employeeAnalysis.metrics.minus_kas.count}x)
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-8 text-center">
                <Users className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">Pilih karyawan untuk melihat analisis detail</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
