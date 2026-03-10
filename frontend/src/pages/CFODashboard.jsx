import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, Users, Building2, 
  AlertTriangle, CheckCircle, BarChart3, PieChart, Activity,
  ArrowUp, ArrowDown, Minus, RefreshCw, Download, Calendar
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import api from '../services/api';

const CFODashboard = () => {
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [profitLoss, setProfitLoss] = useState(null);
  const [cashFlow, setCashFlow] = useState(null);
  const [branchLoss, setBranchLoss] = useState(null);
  const [efficiency, setEfficiency] = useState(null);
  const [period, setPeriod] = useState('month');

  useEffect(() => {
    fetchAllData();
  }, [period]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [dashRes, plRes, cfRes, blRes, efRes] = await Promise.all([
        api.get('/ai-cfo/dashboard'),
        api.get(`/ai-cfo/profit-loss?period=${period}`),
        api.get(`/ai-cfo/cash-flow?period=${period}`),
        api.get('/ai-cfo/branch-loss-analysis'),
        api.get('/ai-cfo/employee-efficiency?analysis_period=3months')
      ]);
      
      setDashboard(dashRes.data);
      setProfitLoss(plRes.data);
      setCashFlow(cfRes.data);
      setBranchLoss(blRes.data);
      setEfficiency(efRes.data);
    } catch (err) {
      console.error('Error fetching CFO data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatRupiah = (num) => {
    if (!num && num !== 0) return 'Rp 0';
    return `Rp ${Math.abs(num).toLocaleString('id-ID')}`;
  };

  const formatPercent = (num) => {
    if (!num && num !== 0) return '0%';
    return `${num.toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="h-8 w-8 animate-spin text-red-500" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="cfo-dashboard">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
            <DollarSign className="h-7 w-7 text-green-400" />
            AI CFO Dashboard
          </h1>
          <p className="text-gray-400 text-sm">Analisis Keuangan & Efisiensi Bisnis</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-40 bg-red-950/30 border-red-900/30">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">Hari Ini</SelectItem>
              <SelectItem value="week">7 Hari</SelectItem>
              <SelectItem value="month">Bulan Ini</SelectItem>
              <SelectItem value="quarter">3 Bulan</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchAllData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-green-900/40 to-green-800/20 border-green-700/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-400">Revenue Bulan</p>
                <p className="text-xl font-bold text-green-400">{formatRupiah(dashboard?.summary?.revenue_month)}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500/50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className={`bg-gradient-to-br ${dashboard?.summary?.net_profit_month >= 0 ? 'from-emerald-900/40 to-emerald-800/20 border-emerald-700/30' : 'from-red-900/40 to-red-800/20 border-red-700/30'}`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-400">Net Profit Bulan</p>
                <p className={`text-xl font-bold ${dashboard?.summary?.net_profit_month >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {dashboard?.summary?.net_profit_month < 0 ? '-' : ''}{formatRupiah(dashboard?.summary?.net_profit_month)}
                </p>
              </div>
              {dashboard?.summary?.net_profit_month >= 0 ? 
                <ArrowUp className="h-8 w-8 text-emerald-500/50" /> : 
                <ArrowDown className="h-8 w-8 text-red-500/50" />
              }
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 border-blue-700/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-400">Total Payroll</p>
                <p className="text-xl font-bold text-blue-400">{formatRupiah(dashboard?.summary?.total_payroll)}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500/50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-amber-900/40 to-amber-800/20 border-amber-700/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-400">Payroll Ratio</p>
                <p className="text-xl font-bold text-amber-400">{formatPercent(dashboard?.summary?.payroll_ratio)}</p>
              </div>
              <PieChart className="h-8 w-8 text-amber-500/50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Employee Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-[#0f0a0a] border-red-900/20">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-amber-400">{dashboard?.summary?.total_employees || 0}</p>
            <p className="text-xs text-gray-400">Total Karyawan</p>
          </CardContent>
        </Card>
        <Card className="bg-[#0f0a0a] border-red-900/20">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-green-400">{dashboard?.summary?.employees_monthly || 0}</p>
            <p className="text-xs text-gray-400">Gaji Bulanan</p>
          </CardContent>
        </Card>
        <Card className="bg-[#0f0a0a] border-red-900/20">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-blue-400">{dashboard?.summary?.employees_daily || 0}</p>
            <p className="text-xs text-gray-400">Gaji Harian</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="pnl" className="space-y-4">
        <TabsList className="bg-red-950/30">
          <TabsTrigger value="pnl">Laba Rugi</TabsTrigger>
          <TabsTrigger value="cashflow">Cash Flow</TabsTrigger>
          <TabsTrigger value="branches">Analisa Cabang</TabsTrigger>
          <TabsTrigger value="efficiency">Efisiensi</TabsTrigger>
        </TabsList>

        {/* Profit & Loss Tab */}
        <TabsContent value="pnl">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <BarChart3 className="h-5 w-5" /> Laporan Laba Rugi
              </CardTitle>
            </CardHeader>
            <CardContent>
              {profitLoss && (
                <div className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <div className="flex justify-between py-2 border-b border-red-900/20">
                        <span className="text-gray-400">Pendapatan (Revenue)</span>
                        <span className="text-green-400 font-semibold">{formatRupiah(profitLoss.revenue?.total)}</span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-red-900/20">
                        <span className="text-gray-400">HPP (COGS)</span>
                        <span className="text-red-400">({formatRupiah(profitLoss.cost_of_goods_sold)})</span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-red-900/30 bg-green-900/20 px-3 rounded">
                        <span className="font-semibold">Laba Kotor</span>
                        <span className="text-green-400 font-bold">{formatRupiah(profitLoss.gross_profit)}</span>
                      </div>
                      <div className="text-xs text-gray-500 text-right">
                        Margin: {formatPercent(profitLoss.gross_margin)}
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="text-sm font-semibold text-gray-300 mb-2">Biaya Operasional:</div>
                      <div className="flex justify-between py-1">
                        <span className="text-gray-400 text-sm">- Gaji & Tunjangan</span>
                        <span className="text-red-400">{formatRupiah(profitLoss.expenses?.payroll)}</span>
                      </div>
                      <div className="flex justify-between py-1">
                        <span className="text-gray-400 text-sm">- Operasional</span>
                        <span className="text-red-400">{formatRupiah(profitLoss.expenses?.operating)}</span>
                      </div>
                      <div className="flex justify-between py-1">
                        <span className="text-gray-400 text-sm">- Lainnya</span>
                        <span className="text-red-400">{formatRupiah(profitLoss.expenses?.other)}</span>
                      </div>
                      <div className={`flex justify-between py-2 px-3 rounded ${profitLoss.net_profit >= 0 ? 'bg-emerald-900/30' : 'bg-red-900/30'}`}>
                        <span className="font-bold">LABA BERSIH</span>
                        <span className={`font-bold text-lg ${profitLoss.net_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {profitLoss.net_profit < 0 ? '-' : ''}{formatRupiah(profitLoss.net_profit)}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 text-right">
                        Net Margin: {formatPercent(profitLoss.net_margin)}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cash Flow Tab */}
        <TabsContent value="cashflow">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Activity className="h-5 w-5" /> Analisis Cash Flow
              </CardTitle>
            </CardHeader>
            <CardContent>
              {cashFlow && (
                <div className="space-y-6">
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="p-4 bg-green-900/20 rounded-lg">
                      <p className="text-xs text-gray-400">Total Cash In</p>
                      <p className="text-2xl font-bold text-green-400">{formatRupiah(cashFlow.inflows?.total)}</p>
                    </div>
                    <div className="p-4 bg-red-900/20 rounded-lg">
                      <p className="text-xs text-gray-400">Total Cash Out</p>
                      <p className="text-2xl font-bold text-red-400">{formatRupiah(cashFlow.outflows?.total)}</p>
                    </div>
                    <div className={`p-4 rounded-lg ${cashFlow.net_cash_flow >= 0 ? 'bg-emerald-900/30' : 'bg-orange-900/30'}`}>
                      <p className="text-xs text-gray-400">Net Cash Flow</p>
                      <p className={`text-2xl font-bold ${cashFlow.net_cash_flow >= 0 ? 'text-emerald-400' : 'text-orange-400'}`}>
                        {cashFlow.net_cash_flow < 0 ? '-' : ''}{formatRupiah(cashFlow.net_cash_flow)}
                      </p>
                    </div>
                  </div>

                  {/* Predictions */}
                  <div className="border-t border-red-900/20 pt-4">
                    <h4 className="font-semibold text-amber-200 mb-3">Prediksi Cash Flow</h4>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className={`p-4 rounded-lg border ${cashFlow.predictions?.next_7_days >= 0 ? 'border-green-700/30 bg-green-900/10' : 'border-red-700/30 bg-red-900/10'}`}>
                        <p className="text-sm text-gray-400">Prediksi 7 Hari</p>
                        <p className={`text-xl font-bold ${cashFlow.predictions?.next_7_days >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {formatRupiah(cashFlow.predictions?.next_7_days)}
                        </p>
                      </div>
                      <div className={`p-4 rounded-lg border ${cashFlow.predictions?.next_30_days >= 0 ? 'border-green-700/30 bg-green-900/10' : 'border-red-700/30 bg-red-900/10'}`}>
                        <p className="text-sm text-gray-400">Prediksi 30 Hari</p>
                        <p className={`text-xl font-bold ${cashFlow.predictions?.next_30_days >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {formatRupiah(cashFlow.predictions?.next_30_days)}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Warnings */}
                  {cashFlow.warnings?.length > 0 && (
                    <div className="space-y-2">
                      {cashFlow.warnings.map((w, idx) => (
                        <div key={idx} className={`p-3 rounded-lg flex items-center gap-3 ${w.level === 'critical' ? 'bg-red-900/30 border border-red-600' : 'bg-yellow-900/30 border border-yellow-600'}`}>
                          <AlertTriangle className={`h-5 w-5 ${w.level === 'critical' ? 'text-red-400' : 'text-yellow-400'}`} />
                          <span className="text-sm">{w.message}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Recommendations */}
                  {cashFlow.recommendations?.length > 0 && (
                    <div className="p-4 bg-blue-900/20 rounded-lg">
                      <h4 className="font-semibold text-blue-300 mb-2">Rekomendasi</h4>
                      <ul className="space-y-1">
                        {cashFlow.recommendations.map((rec, idx) => (
                          <li key={idx} className="text-sm text-gray-300 flex items-center gap-2">
                            <CheckCircle className="h-4 w-4 text-blue-400" /> {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Branch Analysis Tab */}
        <TabsContent value="branches">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Building2 className="h-5 w-5" /> Analisa Cabang Rugi
              </CardTitle>
            </CardHeader>
            <CardContent>
              {branchLoss && (
                <div className="space-y-4">
                  {/* Summary */}
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="p-3 bg-red-900/30 rounded-lg text-center">
                      <p className="text-2xl font-bold text-red-400">{branchLoss.summary?.rugi_berat || 0}</p>
                      <p className="text-xs text-gray-400">Rugi Berat</p>
                    </div>
                    <div className="p-3 bg-orange-900/30 rounded-lg text-center">
                      <p className="text-2xl font-bold text-orange-400">{branchLoss.summary?.rugi_ringan || 0}</p>
                      <p className="text-xs text-gray-400">Rugi Ringan</p>
                    </div>
                    <div className="p-3 bg-yellow-900/30 rounded-lg text-center">
                      <p className="text-2xl font-bold text-yellow-400">{branchLoss.summary?.perlu_perhatian || 0}</p>
                      <p className="text-xs text-gray-400">Perlu Perhatian</p>
                    </div>
                    <div className="p-3 bg-purple-900/30 rounded-lg text-center">
                      <p className="text-xl font-bold text-purple-400">{formatRupiah(branchLoss.total_loss)}</p>
                      <p className="text-xs text-gray-400">Total Kerugian</p>
                    </div>
                  </div>

                  {/* Branch List */}
                  <div className="space-y-3">
                    {branchLoss.branches?.map((branch, idx) => (
                      <div key={idx} className={`p-4 rounded-lg border ${
                        branch.status === 'rugi_berat' ? 'border-red-600 bg-red-900/20' :
                        branch.status === 'rugi_ringan' ? 'border-orange-600 bg-orange-900/20' :
                        'border-yellow-600 bg-yellow-900/20'
                      }`}>
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h4 className="font-semibold text-amber-200">{branch.branch_name}</h4>
                            <span className={`text-xs px-2 py-1 rounded ${
                              branch.status === 'rugi_berat' ? 'bg-red-600 text-white' :
                              branch.status === 'rugi_ringan' ? 'bg-orange-600 text-white' :
                              'bg-yellow-600 text-black'
                            }`}>
                              {branch.status?.replace('_', ' ').toUpperCase()}
                            </span>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold text-red-400">
                              -{formatRupiah(Math.abs(branch.profit))}
                            </p>
                            <p className="text-xs text-gray-400">kerugian/bulan</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-4 gap-3 text-sm mb-3">
                          <div>
                            <p className="text-gray-500">Revenue</p>
                            <p className="text-green-400">{formatRupiah(branch.revenue)}</p>
                          </div>
                          <div>
                            <p className="text-gray-500">Payroll</p>
                            <p className="text-blue-400">{formatRupiah(branch.payroll)}</p>
                          </div>
                          <div>
                            <p className="text-gray-500">Payroll Ratio</p>
                            <p className="text-amber-400">{formatPercent(branch.payroll_ratio)}</p>
                          </div>
                          <div>
                            <p className="text-gray-500">Karyawan</p>
                            <p className="text-purple-400">{branch.employee_count} org</p>
                          </div>
                        </div>

                        {/* Loss Causes */}
                        {branch.loss_causes?.length > 0 && (
                          <div className="mb-2">
                            <p className="text-xs text-gray-500 mb-1">Penyebab:</p>
                            <div className="flex flex-wrap gap-2">
                              {branch.loss_causes.map((cause, i) => (
                                <span key={i} className="text-xs px-2 py-1 bg-red-900/50 text-red-300 rounded">
                                  {cause.cause}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Recommendations */}
                        {branch.recommendations?.length > 0 && (
                          <div className="pt-2 border-t border-red-900/30">
                            <p className="text-xs text-gray-500 mb-1">Rekomendasi:</p>
                            <ul className="text-xs text-gray-300 space-y-1">
                              {branch.recommendations.map((rec, i) => (
                                <li key={i} className="flex items-center gap-1">
                                  <CheckCircle className="h-3 w-3 text-blue-400" /> {rec}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                    
                    {(!branchLoss.branches || branchLoss.branches.length === 0) && (
                      <div className="text-center py-8 text-gray-400">
                        <CheckCircle className="h-12 w-12 mx-auto mb-3 text-green-500" />
                        <p>Tidak ada cabang yang merugi</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Efficiency Tab */}
        <TabsContent value="efficiency">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Users className="h-5 w-5" /> Efisiensi Karyawan per Cabang
              </CardTitle>
            </CardHeader>
            <CardContent>
              {efficiency && (
                <div className="space-y-4">
                  {/* Summary */}
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="p-3 bg-green-900/30 rounded-lg text-center">
                      <p className="text-2xl font-bold text-green-400">{efficiency.summary?.optimal_branches || 0}</p>
                      <p className="text-xs text-gray-400">Optimal</p>
                    </div>
                    <div className="p-3 bg-red-900/30 rounded-lg text-center">
                      <p className="text-2xl font-bold text-red-400">{efficiency.summary?.overstaffed_branches || 0}</p>
                      <p className="text-xs text-gray-400">Kelebihan</p>
                    </div>
                    <div className="p-3 bg-blue-900/30 rounded-lg text-center">
                      <p className="text-2xl font-bold text-blue-400">{efficiency.summary?.understaffed_branches || 0}</p>
                      <p className="text-xs text-gray-400">Kekurangan</p>
                    </div>
                    <div className="p-3 bg-amber-900/30 rounded-lg text-center">
                      <p className="text-2xl font-bold text-amber-400">{efficiency.summary?.potential_efficiency || 0}</p>
                      <p className="text-xs text-gray-400">Potensi Efisiensi</p>
                    </div>
                  </div>

                  {/* Branch List */}
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-red-950/30">
                        <tr className="text-left text-xs text-gray-400">
                          <th className="p-3">Cabang</th>
                          <th className="p-3 text-right">Revenue/bln</th>
                          <th className="p-3 text-center">Saat Ini</th>
                          <th className="p-3 text-center">Ideal</th>
                          <th className="p-3 text-center">Selisih</th>
                          <th className="p-3 text-center">Skor</th>
                          <th className="p-3">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-red-900/20">
                        {efficiency.branches?.map((br, idx) => (
                          <tr key={idx} className="hover:bg-red-950/20">
                            <td className="p-3 font-medium text-amber-200">{br.branch_name}</td>
                            <td className="p-3 text-right text-green-400">{formatRupiah(br.metrics?.monthly_revenue)}</td>
                            <td className="p-3 text-center">{br.headcount?.current}</td>
                            <td className="p-3 text-center text-blue-400">{br.headcount?.ideal}</td>
                            <td className={`p-3 text-center font-semibold ${
                              br.headcount?.difference > 0 ? 'text-red-400' : 
                              br.headcount?.difference < 0 ? 'text-blue-400' : 'text-green-400'
                            }`}>
                              {br.headcount?.difference > 0 ? '+' : ''}{br.headcount?.difference}
                            </td>
                            <td className="p-3 text-center">
                              <span className={`px-2 py-1 rounded text-xs font-bold ${
                                br.efficiency_score >= 80 ? 'bg-green-600' :
                                br.efficiency_score >= 60 ? 'bg-yellow-600 text-black' :
                                'bg-red-600'
                              }`}>
                                {br.efficiency_score}
                              </span>
                            </td>
                            <td className="p-3">
                              <span className={`text-xs px-2 py-1 rounded ${
                                br.status === 'ideal' ? 'bg-green-500/20 text-green-400' :
                                br.status === 'kelebihan' ? 'bg-red-500/20 text-red-400' :
                                'bg-blue-500/20 text-blue-400'
                              }`}>
                                {br.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CFODashboard;
