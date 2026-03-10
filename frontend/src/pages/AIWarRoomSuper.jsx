import React, { useState, useEffect } from 'react';
import { 
  Shield, AlertTriangle, Building2, TrendingUp, TrendingDown,
  Users, Package, MapPin, Target, RefreshCw, Eye, ChevronRight,
  CheckCircle, XCircle, Activity, Zap, AlertOctagon, Store
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import api from '../services/api';

const AIWarRoomSuper = () => {
  const [loading, setLoading] = useState(true);
  const [warroom, setWarroom] = useState(null);
  const [storeViability, setStoreViability] = useState(null);
  const [newBranchRec, setNewBranchRec] = useState(null);
  const [cashierRisk, setCashierRisk] = useState(null);
  const [missingStock, setMissingStock] = useState(null);
  const [fraudDashboard, setFraudDashboard] = useState(null);
  const [period, setPeriod] = useState('3months');

  useEffect(() => {
    fetchAllData();
  }, [period]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [wrRes, svRes, nbRes, crRes, msRes, fdRes] = await Promise.all([
        api.get('/ai-warroom/dashboard'),
        api.get(`/ai-store/branch-viability?period=${period}`),
        api.get('/ai-store/new-branch-recommendation'),
        api.get('/ai-fraud/cashier-risk?period=30days'),
        api.get('/ai-fraud/missing-stock?period=30days'),
        api.get('/ai-fraud/dashboard')
      ]);
      
      setWarroom(wrRes.data);
      setStoreViability(svRes.data);
      setNewBranchRec(nbRes.data);
      setCashierRisk(crRes.data);
      setMissingStock(msRes.data);
      setFraudDashboard(fdRes.data);
    } catch (err) {
      console.error('Error fetching War Room data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatRupiah = (num) => {
    if (!num && num !== 0) return 'Rp 0';
    return `Rp ${Math.abs(num).toLocaleString('id-ID')}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="h-8 w-8 animate-spin text-red-500" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="ai-warroom-super">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
            <Shield className="h-7 w-7 text-red-400" />
            AI Super War Room
          </h1>
          <p className="text-gray-400 text-sm">Command Center - Analisis & Prediksi Bisnis</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-40 bg-red-950/30 border-red-900/30">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="3months">3 Bulan</SelectItem>
              <SelectItem value="6months">6 Bulan</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchAllData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      {/* Alert Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="bg-gradient-to-br from-red-900/50 to-red-800/30 border-red-600">
          <CardContent className="p-4 text-center">
            <AlertOctagon className="h-8 w-8 mx-auto mb-2 text-red-400" />
            <p className="text-2xl font-bold text-red-400">{storeViability?.status_summary?.kritis || 0}</p>
            <p className="text-xs text-gray-400">Cabang Kritis</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-orange-900/40 to-orange-800/20 border-orange-700/30">
          <CardContent className="p-4 text-center">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-orange-400" />
            <p className="text-2xl font-bold text-orange-400">{cashierRisk?.summary?.kritis_count || 0}</p>
            <p className="text-xs text-gray-400">Kasir Risiko Tinggi</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-900/40 to-purple-800/20 border-purple-700/30">
          <CardContent className="p-4 text-center">
            <Package className="h-8 w-8 mx-auto mb-2 text-purple-400" />
            <p className="text-2xl font-bold text-purple-400">{missingStock?.summary?.kritis_count || 0}</p>
            <p className="text-xs text-gray-400">Stok Kritis Hilang</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-900/40 to-green-800/20 border-green-700/30">
          <CardContent className="p-4 text-center">
            <Store className="h-8 w-8 mx-auto mb-2 text-green-400" />
            <p className="text-2xl font-bold text-green-400">{storeViability?.status_summary?.sehat || 0}</p>
            <p className="text-xs text-gray-400">Cabang Sehat</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 border-blue-700/30">
          <CardContent className="p-4 text-center">
            <Target className="h-8 w-8 mx-auto mb-2 text-blue-400" />
            <p className="text-2xl font-bold text-blue-400">
              {newBranchRec?.recommendations?.filter(r => r.potential_score >= 70).length || 0}
            </p>
            <p className="text-xs text-gray-400">Lokasi Potensial</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="stores" className="space-y-4">
        <TabsList className="bg-red-950/30 flex-wrap">
          <TabsTrigger value="stores">Prediksi Toko</TabsTrigger>
          <TabsTrigger value="newbranch">Lokasi Baru</TabsTrigger>
          <TabsTrigger value="cashier">Risiko Kasir</TabsTrigger>
          <TabsTrigger value="stock">Stok Hilang</TabsTrigger>
          <TabsTrigger value="decisions">Keputusan AI</TabsTrigger>
        </TabsList>

        {/* Store Viability Tab */}
        <TabsContent value="stores">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Building2 className="h-5 w-5" /> AI Prediksi Toko Buka/Tutup
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Status Summary */}
                <div className="grid grid-cols-4 gap-4 mb-6">
                  <div className="p-3 bg-green-900/30 rounded-lg text-center">
                    <p className="text-2xl font-bold text-green-400">{storeViability?.status_summary?.sehat || 0}</p>
                    <p className="text-xs text-gray-400">SEHAT</p>
                  </div>
                  <div className="p-3 bg-yellow-900/30 rounded-lg text-center">
                    <p className="text-2xl font-bold text-yellow-400">{storeViability?.status_summary?.warning || 0}</p>
                    <p className="text-xs text-gray-400">WARNING</p>
                  </div>
                  <div className="p-3 bg-orange-900/30 rounded-lg text-center">
                    <p className="text-2xl font-bold text-orange-400">{storeViability?.status_summary?.rugi || 0}</p>
                    <p className="text-xs text-gray-400">RUGI</p>
                  </div>
                  <div className="p-3 bg-red-900/30 rounded-lg text-center">
                    <p className="text-2xl font-bold text-red-400">{storeViability?.status_summary?.kritis || 0}</p>
                    <p className="text-xs text-gray-400">KRITIS</p>
                  </div>
                </div>

                {/* Branch Cards */}
                <div className="space-y-3">
                  {storeViability?.branches?.map((branch, idx) => (
                    <div key={idx} className={`p-4 rounded-lg border ${
                      branch.status === 'KRITIS' ? 'border-red-600 bg-red-900/20' :
                      branch.status === 'RUGI' ? 'border-orange-600 bg-orange-900/20' :
                      branch.status === 'WARNING' ? 'border-yellow-600 bg-yellow-900/20' :
                      'border-green-600 bg-green-900/20'
                    }`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                            branch.status === 'KRITIS' ? 'bg-red-600' :
                            branch.status === 'RUGI' ? 'bg-orange-600' :
                            branch.status === 'WARNING' ? 'bg-yellow-600' :
                            'bg-green-600'
                          }`}>
                            <span className="text-lg font-bold text-white">{branch.score}</span>
                          </div>
                          <div>
                            <h4 className="font-semibold text-amber-200">{branch.branch_name}</h4>
                            <span className={`text-xs px-2 py-1 rounded ${
                              branch.final_recommendation === 'TUTUP' ? 'bg-red-600 text-white' :
                              branch.final_recommendation === 'EFISIENSI_BERAT' ? 'bg-orange-600 text-white' :
                              branch.final_recommendation === 'EFISIENSI' ? 'bg-yellow-600 text-black' :
                              branch.final_recommendation === 'MONITOR' ? 'bg-blue-600 text-white' :
                              'bg-green-600 text-white'
                            }`}>
                              {branch.final_recommendation?.replace('_', ' ')}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-lg font-bold ${branch.metrics?.monthly_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {branch.metrics?.monthly_profit < 0 ? '-' : ''}{formatRupiah(branch.metrics?.monthly_profit)}
                          </p>
                          <p className="text-xs text-gray-400">/bulan</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-5 gap-3 text-sm mb-3">
                        <div>
                          <p className="text-gray-500">Revenue</p>
                          <p className="text-green-400">{formatRupiah(branch.metrics?.monthly_revenue)}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Karyawan</p>
                          <p className="text-blue-400">{branch.metrics?.employee_count}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Payroll Ratio</p>
                          <p className="text-amber-400">{branch.metrics?.payroll_ratio?.toFixed(1)}%</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Margin</p>
                          <p className={branch.metrics?.profit_margin >= 0 ? 'text-green-400' : 'text-red-400'}>
                            {branch.metrics?.profit_margin?.toFixed(1)}%
                          </p>
                        </div>
                        <div>
                          <p className="text-gray-500">Trend</p>
                          <p className={branch.metrics?.trend === 'improving' ? 'text-green-400' : branch.metrics?.trend === 'declining' ? 'text-red-400' : 'text-gray-400'}>
                            {branch.metrics?.trend === 'improving' ? '↗' : branch.metrics?.trend === 'declining' ? '↘' : '→'} {branch.metrics?.trend_percentage?.toFixed(1)}%
                          </p>
                        </div>
                      </div>

                      {/* Issues */}
                      {branch.issues?.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-2">
                          {branch.issues.map((issue, i) => (
                            <span key={i} className="text-xs px-2 py-1 bg-red-900/50 text-red-300 rounded">
                              {issue}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Recommendations */}
                      {branch.recommendations?.length > 0 && (
                        <div className="pt-2 border-t border-red-900/30">
                          <ul className="text-xs text-gray-300 space-y-1">
                            {branch.recommendations.slice(0, 3).map((rec, i) => (
                              <li key={i} className="flex items-center gap-1">
                                <ChevronRight className="h-3 w-3 text-blue-400" /> {rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* New Branch Location Tab */}
        <TabsContent value="newbranch">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <MapPin className="h-5 w-5" /> AI Prediksi Lokasi Cabang Baru
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {newBranchRec?.recommendations?.map((rec, idx) => (
                  <div key={idx} className={`p-4 rounded-lg border ${
                    rec.potential_score >= 80 ? 'border-green-600 bg-green-900/20' :
                    rec.potential_score >= 60 ? 'border-blue-600 bg-blue-900/20' :
                    rec.potential_score >= 40 ? 'border-yellow-600 bg-yellow-900/20' :
                    'border-gray-600 bg-gray-900/20'
                  }`}>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                          rec.potential_score >= 80 ? 'bg-green-600' :
                          rec.potential_score >= 60 ? 'bg-blue-600' :
                          rec.potential_score >= 40 ? 'bg-yellow-600' :
                          'bg-gray-600'
                        }`}>
                          <span className="text-lg font-bold text-white">{rec.potential_score}</span>
                        </div>
                        <div>
                          <h4 className="font-semibold text-amber-200">{rec.region}</h4>
                          <span className={`text-xs px-2 py-1 rounded ${
                            rec.recommendation_level === 'SANGAT_DISARANKAN' ? 'bg-green-600 text-white' :
                            rec.recommendation_level === 'DISARANKAN' ? 'bg-blue-600 text-white' :
                            rec.recommendation_level === 'PERTIMBANGKAN' ? 'bg-yellow-600 text-black' :
                            'bg-gray-600 text-white'
                          }`}>
                            {rec.recommendation_level?.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-green-400">{formatRupiah(rec.estimates?.monthly_sales)}</p>
                        <p className="text-xs text-gray-400">est. penjualan/bln</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-5 gap-3 text-sm mb-3">
                      <div>
                        <p className="text-gray-500">Cabang Existing</p>
                        <p className="text-blue-400">{rec.existing_branches}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Avg Revenue</p>
                        <p className="text-green-400">{formatRupiah(rec.avg_monthly_revenue)}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Est. Karyawan</p>
                        <p className="text-purple-400">{rec.estimates?.initial_employees}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Startup Cost</p>
                        <p className="text-amber-400">{formatRupiah(rec.estimates?.startup_cost)}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Est. BEP</p>
                        <p className="text-cyan-400">{rec.estimates?.bep_months} bulan</p>
                      </div>
                    </div>

                    {rec.notes?.length > 0 && (
                      <div className="text-xs text-gray-400 italic">
                        {rec.notes.join(', ')}
                      </div>
                    )}

                    {rec.existing_branch_names?.length > 0 && (
                      <div className="mt-2 text-xs text-gray-500">
                        Cabang existing: {rec.existing_branch_names.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cashier Risk Tab */}
        <TabsContent value="cashier">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Users className="h-5 w-5" /> AI Deteksi Risiko Kasir
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Summary */}
                <div className="grid grid-cols-4 gap-4 mb-6">
                  <div className="p-3 bg-red-900/30 rounded-lg text-center">
                    <p className="text-2xl font-bold text-red-400">{cashierRisk?.summary?.kritis_count || 0}</p>
                    <p className="text-xs text-gray-400">KRITIS</p>
                  </div>
                  <div className="p-3 bg-orange-900/30 rounded-lg text-center">
                    <p className="text-2xl font-bold text-orange-400">{cashierRisk?.summary?.tinggi_count || 0}</p>
                    <p className="text-xs text-gray-400">TINGGI</p>
                  </div>
                  <div className="p-3 bg-yellow-900/30 rounded-lg text-center">
                    <p className="text-2xl font-bold text-yellow-400">{cashierRisk?.summary?.sedang_count || 0}</p>
                    <p className="text-xs text-gray-400">SEDANG</p>
                  </div>
                  <div className="p-3 bg-green-900/30 rounded-lg text-center">
                    <p className="text-2xl font-bold text-green-400">{cashierRisk?.summary?.rendah_count || 0}</p>
                    <p className="text-xs text-gray-400">RENDAH</p>
                  </div>
                </div>

                {/* High Risk Branches */}
                {cashierRisk?.high_risk_branches?.length > 0 && (
                  <div className="p-4 bg-red-900/20 rounded-lg mb-4">
                    <h4 className="font-semibold text-red-400 mb-2">Cabang Rawan:</h4>
                    <div className="flex flex-wrap gap-2">
                      {cashierRisk.high_risk_branches.map((br, i) => (
                        <span key={i} className="px-3 py-1 bg-red-900/50 rounded text-sm">
                          {br.branch} ({br.high_risk_count} org)
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Employee List */}
                <div className="space-y-3">
                  {cashierRisk?.employees?.filter(e => e.risk_score > 0).slice(0, 20).map((emp, idx) => (
                    <div key={idx} className={`p-4 rounded-lg border ${
                      emp.risk_level === 'KRITIS' ? 'border-red-600 bg-red-900/20' :
                      emp.risk_level === 'TINGGI' ? 'border-orange-600 bg-orange-900/20' :
                      emp.risk_level === 'SEDANG' ? 'border-yellow-600 bg-yellow-900/20' :
                      'border-green-600 bg-green-900/10'
                    }`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            emp.risk_level === 'KRITIS' ? 'bg-red-600' :
                            emp.risk_level === 'TINGGI' ? 'bg-orange-600' :
                            emp.risk_level === 'SEDANG' ? 'bg-yellow-600' :
                            'bg-green-600'
                          }`}>
                            <span className="font-bold text-white">{emp.risk_score}</span>
                          </div>
                          <div>
                            <h4 className="font-semibold text-amber-200">{emp.employee_name}</h4>
                            <p className="text-xs text-gray-400">{emp.branch_name}</p>
                          </div>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded ${
                          emp.risk_level === 'KRITIS' ? 'bg-red-600' :
                          emp.risk_level === 'TINGGI' ? 'bg-orange-600' :
                          emp.risk_level === 'SEDANG' ? 'bg-yellow-600 text-black' :
                          'bg-green-600'
                        }`}>
                          {emp.risk_level}
                        </span>
                      </div>

                      <div className="grid grid-cols-4 gap-3 text-xs mb-2">
                        <div>
                          <p className="text-gray-500">Minus Kas</p>
                          <p className="text-red-400">{emp.metrics?.minus_count}x ({formatRupiah(emp.metrics?.total_minus)})</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Void</p>
                          <p className="text-orange-400">{emp.metrics?.void_count}x ({formatRupiah(emp.metrics?.total_void)})</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Refund</p>
                          <p className="text-purple-400">{emp.metrics?.refund_count}x</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Trans. Abnormal</p>
                          <p className="text-cyan-400">{emp.metrics?.abnormal_hour_transactions}x</p>
                        </div>
                      </div>

                      {emp.indicators?.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {emp.indicators.map((ind, i) => (
                            <span key={i} className="text-xs px-2 py-1 bg-red-900/50 text-red-300 rounded">
                              {ind}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="mt-2 text-xs text-blue-400">
                        Rekomendasi: {emp.recommendation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Missing Stock Tab */}
        <TabsContent value="stock">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Package className="h-5 w-5" /> AI Deteksi Stok Hilang
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Summary */}
                <div className="grid grid-cols-4 gap-4 mb-6">
                  <div className="p-3 bg-red-900/30 rounded-lg text-center">
                    <p className="text-2xl font-bold text-red-400">{missingStock?.summary?.kritis_count || 0}</p>
                    <p className="text-xs text-gray-400">KRITIS</p>
                  </div>
                  <div className="p-3 bg-orange-900/30 rounded-lg text-center">
                    <p className="text-2xl font-bold text-orange-400">{missingStock?.summary?.tinggi_count || 0}</p>
                    <p className="text-xs text-gray-400">TINGGI</p>
                  </div>
                  <div className="p-3 bg-purple-900/30 rounded-lg text-center">
                    <p className="text-xl font-bold text-purple-400">{formatRupiah(missingStock?.summary?.total_estimated_loss)}</p>
                    <p className="text-xs text-gray-400">Est. Kerugian</p>
                  </div>
                  <div className="p-3 bg-blue-900/30 rounded-lg text-center">
                    <p className="text-2xl font-bold text-blue-400">{missingStock?.summary?.total_items_analyzed || 0}</p>
                    <p className="text-xs text-gray-400">Item Dianalisis</p>
                  </div>
                </div>

                {/* Risky Branches */}
                {missingStock?.risky_branches?.length > 0 && (
                  <div className="p-4 bg-purple-900/20 rounded-lg mb-4">
                    <h4 className="font-semibold text-purple-400 mb-2">Cabang dengan Kehilangan Tertinggi:</h4>
                    <div className="space-y-2">
                      {missingStock.risky_branches.map((br, i) => (
                        <div key={i} className="flex justify-between items-center px-3 py-2 bg-purple-900/30 rounded">
                          <span>{br.branch}</span>
                          <div className="text-right">
                            <span className="text-red-400 font-semibold">{formatRupiah(br.total_loss)}</span>
                            <span className="text-xs text-gray-400 ml-2">({br.item_count} item)</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Items */}
                <div className="space-y-3">
                  {missingStock?.items?.slice(0, 15).map((item, idx) => (
                    <div key={idx} className={`p-4 rounded-lg border ${
                      item.status === 'KRITIS' ? 'border-red-600 bg-red-900/20' :
                      item.status === 'TINGGI' ? 'border-orange-600 bg-orange-900/20' :
                      item.status === 'WARNING' ? 'border-yellow-600 bg-yellow-900/20' :
                      'border-green-600 bg-green-900/10'
                    }`}>
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <h4 className="font-semibold text-amber-200">{item.product_name}</h4>
                          <p className="text-xs text-gray-400">{item.branch_name}</p>
                        </div>
                        <div className="text-right">
                          <span className={`text-xs px-2 py-1 rounded ${
                            item.status === 'KRITIS' ? 'bg-red-600' :
                            item.status === 'TINGGI' ? 'bg-orange-600' :
                            item.status === 'WARNING' ? 'bg-yellow-600 text-black' :
                            'bg-green-600'
                          }`}>
                            {item.status}
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-4 gap-3 text-sm">
                        <div>
                          <p className="text-gray-500">Total Hilang</p>
                          <p className="text-red-400">{item.total_missing} unit</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Kejadian</p>
                          <p className="text-orange-400">{item.missing_incidents}x</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Est. Kerugian</p>
                          <p className="text-purple-400">{formatRupiah(item.estimated_loss)}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Risk Score</p>
                          <p className="text-amber-400">{item.risk_score}</p>
                        </div>
                      </div>

                      <div className="mt-2 text-xs text-blue-400">
                        {item.recommendation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Decisions Tab */}
        <TabsContent value="decisions">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Zap className="h-5 w-5" /> Keputusan & Rekomendasi AI
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {warroom?.ai_recommendations?.map((rec, idx) => (
                  <div key={idx} className={`p-4 rounded-lg border ${
                    rec.priority === 'high' ? 'border-red-600 bg-red-900/20' :
                    rec.priority === 'medium' ? 'border-yellow-600 bg-yellow-900/20' :
                    'border-blue-600 bg-blue-900/20'
                  }`}>
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-2 py-1 text-xs rounded ${
                        rec.priority === 'high' ? 'bg-red-600' :
                        rec.priority === 'medium' ? 'bg-yellow-600 text-black' :
                        'bg-blue-600'
                      }`}>
                        {rec.priority?.toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-400">{rec.type}</span>
                    </div>
                    <p className="text-amber-200 font-medium">{rec.message}</p>
                    <p className="text-sm text-gray-400 mt-1">{rec.action}</p>
                  </div>
                ))}

                {/* Problem Branches */}
                {warroom?.problem_branches?.length > 0 && (
                  <div className="p-4 bg-orange-900/20 rounded-lg">
                    <h4 className="font-semibold text-orange-400 mb-3">Cabang Butuh Perhatian</h4>
                    <div className="space-y-2">
                      {warroom.problem_branches.map((br, i) => (
                        <div key={i} className="flex justify-between items-center py-2 border-b border-orange-900/30">
                          <span>{br.branch_name}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-green-400">{formatRupiah(br.total_sales_month)}</span>
                            <span className={`text-xs px-2 py-1 rounded ${
                              br.status === 'KRITIS' ? 'bg-red-600' :
                              br.status === 'WARNING' ? 'bg-yellow-600 text-black' :
                              'bg-blue-600'
                            }`}>
                              {br.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Low Stock Alerts */}
                {warroom?.low_stock_alerts?.length > 0 && (
                  <div className="p-4 bg-purple-900/20 rounded-lg">
                    <h4 className="font-semibold text-purple-400 mb-3">Alert Stok Rendah</h4>
                    <div className="grid md:grid-cols-2 gap-3">
                      {warroom.low_stock_alerts.slice(0, 6).map((item, i) => (
                        <div key={i} className="p-3 bg-purple-900/30 rounded flex justify-between items-center">
                          <div>
                            <p className="text-sm text-amber-200">{item.product_name}</p>
                            <p className="text-xs text-gray-400">Stok: {item.current_stock} / Min: {item.min_stock}</p>
                          </div>
                          <span className="text-xs text-red-400">{item.days_until_empty} hari</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AIWarRoomSuper;
