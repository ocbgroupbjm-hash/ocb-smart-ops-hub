import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Brain, TrendingUp, AlertTriangle, Lightbulb, BarChart2,
  DollarSign, Users, Package, Building2, RefreshCw,
  AlertCircle, CheckCircle, Activity, Target, Eye
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const AICommandCenter = () => {
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [trends, setTrends] = useState(null);
  const [anomalies, setAnomalies] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashRes, recRes, trendRes, anomRes] = await Promise.all([
        axios.get(`${API}/api/ai-command/dashboard`),
        axios.get(`${API}/api/ai-command/recommendations`),
        axios.get(`${API}/api/ai-command/trends?days=30`),
        axios.get(`${API}/api/ai-command/anomalies`)
      ]);
      
      setDashboard(dashRes.data);
      setRecommendations(recRes.data);
      setTrends(trendRes.data);
      setAnomalies(anomRes.data);
    } catch (err) {
      console.error('Error fetching AI data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(amount);
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'bg-red-600';
      case 'high': return 'bg-orange-600';
      case 'warning': return 'bg-yellow-600';
      case 'medium': return 'bg-blue-600';
      default: return 'bg-gray-600';
    }
  };

  const getInsightIcon = (type) => {
    switch (type) {
      case 'positive': return <CheckCircle className="h-5 w-5 text-green-400" />;
      case 'warning': return <AlertTriangle className="h-5 w-5 text-yellow-400" />;
      case 'critical': return <AlertCircle className="h-5 w-5 text-red-400" />;
      default: return <Activity className="h-5 w-5 text-blue-400" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0608] to-[#1a0a0e] p-4" data-testid="ai-command-center-page">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
              <Brain className="h-6 w-6 text-purple-400" />
              AI Command Center
            </h1>
            <p className="text-sm text-gray-400">Analisis bisnis & rekomendasi strategis berbasis AI</p>
          </div>
          <Button 
            onClick={fetchData} 
            disabled={loading}
            className="bg-purple-900/50 hover:bg-purple-800/50 text-purple-100"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh Analysis
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <Card className="bg-gradient-to-br from-green-900/30 to-green-950/50 border-green-700/30">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-green-300">Penjualan Hari Ini</p>
                  <p className="text-xl font-bold text-green-400">{formatCurrency(dashboard.financials?.sales_today || 0)}</p>
                </div>
                <DollarSign className="h-8 w-8 text-green-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-blue-900/30 to-blue-950/50 border-blue-700/30">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-blue-300">Tingkat Kehadiran</p>
                  <p className="text-xl font-bold text-blue-400">{dashboard.summary?.attendance_rate || 0}%</p>
                </div>
                <Users className="h-8 w-8 text-blue-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-yellow-900/30 to-yellow-950/50 border-yellow-700/30">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-yellow-300">Stok Rendah</p>
                  <p className="text-xl font-bold text-yellow-400">{dashboard.inventory?.low_stock_count || 0}</p>
                </div>
                <Package className="h-8 w-8 text-yellow-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-red-900/30 to-red-950/50 border-red-700/30">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-red-300">Minus Kas</p>
                  <p className="text-xl font-bold text-red-400">{formatCurrency(Math.abs(dashboard.financials?.minus_today || 0))}</p>
                </div>
                <AlertCircle className="h-8 w-8 text-red-500/50" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-4">
          {/* AI Insights */}
          <Card className="bg-[#120a0c]/80 border-purple-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Eye className="h-5 w-5 text-purple-400" />
                AI Insights
                {dashboard?.insights_count && (
                  <div className="flex gap-1 ml-auto">
                    {dashboard.insights_count.critical > 0 && (
                      <Badge className="bg-red-600">{dashboard.insights_count.critical} Critical</Badge>
                    )}
                    {dashboard.insights_count.warning > 0 && (
                      <Badge className="bg-yellow-600">{dashboard.insights_count.warning} Warning</Badge>
                    )}
                  </div>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {dashboard?.insights?.map((insight, idx) => (
                  <div 
                    key={idx}
                    className={`p-3 rounded-lg border ${
                      insight.type === 'critical' ? 'bg-red-900/20 border-red-700/30' :
                      insight.type === 'warning' ? 'bg-yellow-900/20 border-yellow-700/30' :
                      'bg-green-900/20 border-green-700/30'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      {getInsightIcon(insight.type)}
                      <div>
                        <p className="font-medium text-amber-100">{insight.title}</p>
                        <p className="text-sm text-gray-400">{insight.message}</p>
                      </div>
                    </div>
                  </div>
                ))}
                {(!dashboard?.insights || dashboard.insights.length === 0) && (
                  <div className="text-center py-6">
                    <CheckCircle className="h-10 w-10 mx-auto text-green-500/50 mb-2" />
                    <p className="text-gray-400">Semua operasional berjalan normal</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card className="bg-[#120a0c]/80 border-blue-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-yellow-400" />
                AI Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recommendations?.recommendations?.map((rec) => (
                  <div key={rec.id} className="p-3 rounded-lg bg-blue-900/10 border border-blue-700/20">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-medium text-amber-100">{rec.title}</p>
                        <p className="text-sm text-gray-400">{rec.description}</p>
                      </div>
                      <Badge className={getPriorityColor(rec.priority)}>{rec.priority}</Badge>
                    </div>
                    <div className="mt-2 p-2 bg-black/30 rounded">
                      <p className="text-xs text-blue-300"><strong>Aksi:</strong> {rec.action}</p>
                      <p className="text-xs text-green-300 mt-1"><strong>Impact:</strong> {rec.impact}</p>
                    </div>
                    {rec.branches && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {rec.branches.map((b, i) => (
                          <Badge key={i} variant="outline" className="text-xs">{b}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Side Panel */}
        <div className="space-y-4">
          {/* Trend Analysis */}
          <Card className="bg-[#120a0c]/80 border-green-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-400" />
                Trend 30 Hari
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Trend Penjualan</span>
                  <div className="flex items-center gap-1">
                    {trends?.trend_direction === 'up' && <TrendingUp className="h-4 w-4 text-green-400" />}
                    {trends?.trend_direction === 'down' && <TrendingUp className="h-4 w-4 text-red-400 rotate-180" />}
                    <span className={`font-bold ${
                      trends?.sales_trend_percentage > 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {trends?.sales_trend_percentage > 0 ? '+' : ''}{trends?.sales_trend_percentage || 0}%
                    </span>
                  </div>
                </div>
                <div className="p-2 bg-red-950/30 rounded">
                  <p className="text-xs text-gray-400">Total Penjualan</p>
                  <p className="text-lg font-bold text-amber-100">{formatCurrency(trends?.summary?.total_sales || 0)}</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 bg-red-950/30 rounded">
                    <p className="text-xs text-gray-400">Rata-rata Harian</p>
                    <p className="text-sm font-bold text-amber-100">{formatCurrency(trends?.summary?.avg_daily_sales || 0)}</p>
                  </div>
                  <div className="p-2 bg-red-950/30 rounded">
                    <p className="text-xs text-gray-400">Total Transaksi</p>
                    <p className="text-sm font-bold text-amber-100">{trends?.summary?.total_transactions || 0}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Anomalies */}
          <Card className="bg-[#120a0c]/80 border-orange-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-orange-400" />
                Anomaly Detection ({anomalies?.total_anomalies || 0})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {anomalies?.anomalies?.map((anomaly, idx) => (
                  <div key={idx} className={`p-2 rounded border ${
                    anomaly.severity === 'high' ? 'bg-red-900/20 border-red-700/30' : 'bg-orange-900/20 border-orange-700/30'
                  }`}>
                    <div className="flex items-start gap-2">
                      <AlertCircle className={`h-4 w-4 mt-0.5 ${anomaly.severity === 'high' ? 'text-red-400' : 'text-orange-400'}`} />
                      <div>
                        <p className="text-xs font-medium text-amber-100">{anomaly.entity_name}</p>
                        <p className="text-xs text-gray-400">{anomaly.description}</p>
                        <p className="text-xs text-blue-300 mt-1">{anomaly.recommended_action}</p>
                      </div>
                    </div>
                  </div>
                ))}
                {(!anomalies?.anomalies || anomalies.anomalies.length === 0) && (
                  <div className="text-center py-4">
                    <CheckCircle className="h-8 w-8 mx-auto text-green-500/50 mb-1" />
                    <p className="text-xs text-gray-400">Tidak ada anomali terdeteksi</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                <BarChart2 className="h-4 w-4" />
                Status Hari Ini
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Total Cabang</span>
                  <span className="text-sm font-bold text-amber-100">{dashboard?.summary?.total_branches || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Sudah Lapor</span>
                  <span className="text-sm font-bold text-green-400">{dashboard?.summary?.branches_reported_today || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Karyawan Aktif</span>
                  <span className="text-sm font-bold text-amber-100">{dashboard?.summary?.total_employees || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Tingkat Telat</span>
                  <span className={`text-sm font-bold ${dashboard?.summary?.late_rate > 20 ? 'text-red-400' : 'text-green-400'}`}>
                    {dashboard?.summary?.late_rate || 0}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AICommandCenter;
