import React, { useState, useEffect } from 'react';
import { 
  Activity, Building2, Users, DollarSign, AlertTriangle, TrendingUp,
  Clock, Bell, Eye, Zap, Target, Award, AlertCircle, RefreshCw,
  ChevronRight, ArrowUp, ArrowDown
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const WarRoomV2 = () => {
  const { toast } = useToast();
  const [data, setData] = useState(null);
  const [fraudAlerts, setFraudAlerts] = useState([]);
  const [insights, setInsights] = useState([]);
  const [liveFeed, setLiveFeed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchAllData();
    // Auto refresh every 30 seconds
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    try {
      setRefreshing(true);
      const [dashboardRes, fraudRes, insightsRes, feedRes] = await Promise.all([
        api.get('/api/war-room/dashboard'),
        api.get('/api/war-room/fraud-detection'),
        api.get('/api/war-room/ai-insights'),
        api.get('/api/war-room/live-feed?limit=10')
      ]);
      
      setData(dashboardRes.data);
      setFraudAlerts(fraudRes.data.alerts || []);
      setInsights(insightsRes.data.insights || []);
      setLiveFeed(feedRes.data.activities || []);
      setLoading(false);
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat data', variant: 'destructive' });
      setLoading(false);
    } finally {
      setRefreshing(false);
    }
  };

  const formatRupiah = (num) => {
    if (num >= 1000000000) return `Rp ${(num / 1000000000).toFixed(1)}M`;
    if (num >= 1000000) return `Rp ${(num / 1000000).toFixed(1)}Jt`;
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'text-red-400 bg-red-500/20 border-red-700/30',
      urgent: 'text-orange-400 bg-orange-500/20 border-orange-700/30',
      warning: 'text-yellow-400 bg-yellow-500/20 border-yellow-700/30',
      info: 'text-blue-400 bg-blue-500/20 border-blue-700/30'
    };
    return colors[severity] || colors.info;
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Activity className="h-12 w-12 text-amber-400 mx-auto animate-pulse mb-4" />
          <p className="text-gray-400">Loading War Room...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="war-room-v2-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent">
            WAR ROOM COMMAND CENTER
          </h1>
          <p className="text-gray-400 text-sm">Real-time monitoring untuk Owner | {data?.tanggal}</p>
        </div>
        <Button 
          variant="outline" 
          onClick={fetchAllData}
          disabled={refreshing}
          className="border-amber-700/30"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Critical Alerts Banner */}
      {data?.alerts?.critical > 0 && (
        <div className="p-4 bg-red-900/30 border border-red-700/50 rounded-lg flex items-center gap-4 animate-pulse">
          <AlertTriangle className="h-8 w-8 text-red-400" />
          <div>
            <p className="text-red-400 font-bold">{data.alerts.critical} ALERT CRITICAL!</p>
            <p className="text-sm text-gray-400">Segera periksa dan tindak lanjuti</p>
          </div>
          <Button variant="destructive" size="sm" className="ml-auto">
            Lihat Semua <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}

      {/* Main KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card className="bg-gradient-to-br from-green-900/30 to-green-800/20 border-green-700/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <DollarSign className="h-5 w-5 text-green-400" />
              <span className="text-xs text-green-400">Hari Ini</span>
            </div>
            <p className="text-xl font-bold text-green-400">{formatRupiah(data?.sales_today?.penjualan)}</p>
            <p className="text-xs text-gray-400">{data?.sales_today?.transaksi} transaksi</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border-blue-700/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <Target className="h-5 w-5 text-blue-400" />
              <span className="text-xs text-blue-400">MTD</span>
            </div>
            <p className="text-xl font-bold text-blue-400">{formatRupiah(data?.sales_mtd?.penjualan)}</p>
            <p className="text-xs text-gray-400">{data?.sales_mtd?.achievement}% target</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-900/30 to-amber-800/20 border-amber-700/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <Building2 className="h-5 w-5 text-amber-400" />
              <span className={`text-xs ${data?.overview?.cabang_belum_setor > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {data?.overview?.cabang_belum_setor > 0 ? `${data?.overview?.cabang_belum_setor} pending` : 'OK'}
              </span>
            </div>
            <p className="text-xl font-bold text-amber-400">{data?.overview?.cabang_sudah_setor}/{data?.overview?.total_cabang}</p>
            <p className="text-xs text-gray-400">Cabang setor</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border-purple-700/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <Users className="h-5 w-5 text-purple-400" />
              <span className="text-xs text-purple-400">{data?.overview?.karyawan_telat} telat</span>
            </div>
            <p className="text-xl font-bold text-purple-400">{data?.overview?.karyawan_hadir}/{data?.overview?.total_karyawan}</p>
            <p className="text-xs text-gray-400">Kehadiran</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-900/30 to-red-800/20 border-red-700/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              <ArrowDown className="h-4 w-4 text-red-400" />
            </div>
            <p className="text-xl font-bold text-red-400">{formatRupiah(data?.setoran_today?.total_minus)}</p>
            <p className="text-xs text-gray-400">Minus hari ini</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-cyan-900/30 to-cyan-800/20 border-cyan-700/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <Zap className="h-5 w-5 text-cyan-400" />
              <ArrowUp className="h-4 w-4 text-cyan-400" />
            </div>
            <p className="text-xl font-bold text-cyan-400">{formatRupiah(data?.setoran_today?.total_plus)}</p>
            <p className="text-xs text-gray-400">Plus hari ini</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Rankings */}
        <div className="space-y-4">
          {/* Top Branches */}
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-amber-200 flex items-center gap-2">
                <Award className="h-4 w-4 text-amber-400" /> Top 5 Cabang
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {data?.rankings?.top_cabang?.length > 0 ? data.rankings.top_cabang.map((branch, idx) => (
                <div key={branch.branch_id} className="flex items-center gap-3 p-2 bg-green-900/10 rounded-lg">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    idx === 0 ? 'bg-amber-500 text-black' : idx === 1 ? 'bg-gray-400 text-black' : idx === 2 ? 'bg-amber-700 text-white' : 'bg-gray-600 text-white'
                  }`}>{idx + 1}</span>
                  <div className="flex-1">
                    <p className="text-sm text-gray-200">{branch.branch_name}</p>
                    <p className="text-xs text-gray-500">{branch.total_transaksi} trx</p>
                  </div>
                  <p className="text-sm font-bold text-green-400">{formatRupiah(branch.total_penjualan)}</p>
                </div>
              )) : (
                <p className="text-gray-500 text-sm text-center py-4">Belum ada data</p>
              )}
            </CardContent>
          </Card>

          {/* Problem Employees */}
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-red-400 flex items-center gap-2">
                <AlertCircle className="h-4 w-4" /> Karyawan Bermasalah
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {data?.rankings?.karyawan_bermasalah?.length > 0 ? data.rankings.karyawan_bermasalah.slice(0, 5).map((emp) => (
                <div key={emp.employee_id} className="flex items-center gap-3 p-2 bg-red-900/10 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm text-gray-200">{emp.employee_name}</p>
                    <p className="text-xs text-gray-500">{emp.count}x minus</p>
                  </div>
                  <p className="text-sm font-bold text-red-400">{formatRupiah(emp.total_minus)}</p>
                </div>
              )) : (
                <p className="text-green-400 text-sm text-center py-4">Tidak ada masalah</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Middle Column - AI Insights & Fraud */}
        <div className="space-y-4">
          {/* AI Insights */}
          <Card className="bg-[#0f0a0a] border-purple-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400 flex items-center gap-2">
                <Zap className="h-4 w-4" /> AI Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {insights.map((insight, idx) => (
                <div key={idx} className={`p-3 rounded-lg border ${getSeverityColor(insight.severity)}`}>
                  <p className="text-sm font-medium">{insight.title}</p>
                  <p className="text-xs text-gray-400 mt-1">{insight.summary}</p>
                  <p className="text-xs mt-2 opacity-75">{insight.recommendation}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Fraud Detection */}
          <Card className="bg-[#0f0a0a] border-red-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-red-400 flex items-center gap-2">
                <Eye className="h-4 w-4" /> Fraud Detection
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 max-h-60 overflow-y-auto">
              {fraudAlerts.length > 0 ? fraudAlerts.slice(0, 5).map((alert, idx) => (
                <div key={idx} className={`p-3 rounded-lg border ${getSeverityColor(alert.severity)}`}>
                  <div className="flex items-start gap-2">
                    <span className={`px-1.5 py-0.5 text-[10px] rounded ${alert.severity === 'critical' ? 'bg-red-600' : 'bg-yellow-600'}`}>
                      {alert.pattern}
                    </span>
                  </div>
                  <p className="text-xs mt-2">{alert.message}</p>
                </div>
              )) : (
                <p className="text-green-400 text-sm text-center py-4">Tidak ada fraud terdeteksi</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Live Feed & Chart */}
        <div className="space-y-4">
          {/* Live Feed */}
          <Card className="bg-[#0f0a0a] border-green-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-green-400 flex items-center gap-2">
                <Activity className="h-4 w-4" /> Live Feed
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse ml-auto"></span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 max-h-80 overflow-y-auto">
              {liveFeed.map((activity, idx) => (
                <div key={idx} className={`p-2 rounded-lg border ${getSeverityColor(activity.severity)} bg-opacity-10`}>
                  <div className="flex items-start gap-2">
                    <span className={`px-1.5 py-0.5 text-[10px] rounded uppercase ${
                      activity.type === 'alert' ? 'bg-red-600/50' : 
                      activity.type === 'setoran' ? 'bg-green-600/50' : 'bg-blue-600/50'
                    }`}>
                      {activity.type}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">{activity.title}</p>
                      <p className="text-[10px] text-gray-500 truncate">{activity.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Mini Chart - 7 Day Trend */}
          <Card className="bg-[#0f0a0a] border-blue-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-blue-400 flex items-center gap-2">
                <TrendingUp className="h-4 w-4" /> Trend 7 Hari
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between h-24 gap-1">
                {data?.trends?.penjualan_7_hari?.map((day, idx) => {
                  const maxVal = Math.max(...data.trends.penjualan_7_hari.map(d => d.total));
                  const height = maxVal > 0 ? (day.total / maxVal) * 100 : 0;
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                      <div 
                        className="w-full bg-gradient-to-t from-blue-600 to-blue-400 rounded-t"
                        style={{ height: `${Math.max(height, 5)}%` }}
                      />
                      <span className="text-[10px] text-gray-500">
                        {new Date(day.tanggal).toLocaleDateString('id-ID', { weekday: 'short' })}
                      </span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* MTD Summary */}
          <Card className="bg-gradient-to-br from-amber-900/20 to-amber-800/10 border-amber-700/30">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-gray-400">Target Bulan Ini</span>
                <span className="text-2xl font-bold text-amber-400">{data?.sales_mtd?.achievement}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="h-2 rounded-full bg-gradient-to-r from-amber-600 to-amber-400"
                  style={{ width: `${Math.min(data?.sales_mtd?.achievement || 0, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-2">
                <span>{formatRupiah(data?.sales_mtd?.penjualan)}</span>
                <span>{formatRupiah(data?.sales_mtd?.target)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default WarRoomV2;
