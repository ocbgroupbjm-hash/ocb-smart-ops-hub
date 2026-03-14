import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  TrendingUp, TrendingDown, Minus, RefreshCw, AlertTriangle,
  DollarSign, Package, ShoppingCart, Users, BarChart3,
  Brain, Lightbulb, Target, Shield, Download
} from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

const CEODashboardAI = () => {
  const { token, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [salesData, setSalesData] = useState(null);
  const [inventoryData, setInventoryData] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch CEO Summary
      const ceoRes = await fetch(`${API}/api/ai/ceo/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (ceoRes.ok) {
        setData(await ceoRes.json());
      }

      // Fetch Sales AI
      const salesRes = await fetch(`${API}/api/ai/sales/report?days=30`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (salesRes.ok) {
        setSalesData(await salesRes.json());
      }

      // Fetch Inventory AI
      const invRes = await fetch(`${API}/api/ai/inventory/report`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (invRes.ok) {
        setInventoryData(await invRes.json());
      }

    } catch (err) {
      toast.error('Gagal memuat AI Dashboard');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getTrendIcon = (direction) => {
    if (direction === 'NAIK') return <TrendingUp className="w-5 h-5 text-green-500" />;
    if (direction === 'TURUN') return <TrendingDown className="w-5 h-5 text-red-500" />;
    return <Minus className="w-5 h-5 text-gray-500" />;
  };

  const getHealthBadge = (health) => {
    const colors = {
      'GOOD': 'bg-green-100 text-green-800',
      'ATTENTION': 'bg-yellow-100 text-yellow-800',
      'CRITICAL': 'bg-red-100 text-red-800'
    };
    return <Badge className={colors[health] || 'bg-gray-100'}>{health}</Badge>;
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0
    }).format(val || 0);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="flex items-center gap-3 text-white">
          <Brain className="w-8 h-8 animate-pulse text-purple-400" />
          <span className="text-xl">AI sedang menganalisis data...</span>
        </div>
      </div>
    );
  }

  const exec = data?.executive_summary || {};
  const insights = data?.insights || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-6" data-testid="ceo-dashboard-ai">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-purple-600 rounded-xl">
            <Brain className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">CEO AI Dashboard</h1>
            <p className="text-purple-300">Powered by OCB TITAN AI Engine</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Badge className="bg-purple-600 text-white px-4 py-2">
            <Shield className="w-4 h-4 mr-2" />
            READ ONLY MODE
          </Badge>
          <Button variant="outline" onClick={fetchData} className="border-purple-500 text-purple-300 hover:bg-purple-800">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Executive Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Sales Growth */}
        <Card className="bg-gray-800/50 border-gray-700 backdrop-blur" data-testid="sales-growth-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <ShoppingCart className="w-8 h-8 text-blue-400" />
              {getTrendIcon(exec.sales_growth?.direction)}
            </div>
            <h3 className="text-gray-400 text-sm mb-1">Sales Trend</h3>
            <p className="text-2xl font-bold text-white">{exec.sales_growth?.direction || 'N/A'}</p>
            <p className="text-sm text-gray-500">{exec.sales_growth?.percentage || 0}% perubahan</p>
          </CardContent>
        </Card>

        {/* Profit Margin */}
        <Card className="bg-gray-800/50 border-gray-700 backdrop-blur" data-testid="profit-margin-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <DollarSign className="w-8 h-8 text-green-400" />
              <Badge className={exec.profit_margin > 20 ? 'bg-green-600' : exec.profit_margin > 10 ? 'bg-yellow-600' : 'bg-red-600'}>
                {exec.profit_margin > 20 ? 'SEHAT' : exec.profit_margin > 10 ? 'PERLU PERHATIAN' : 'RENDAH'}
              </Badge>
            </div>
            <h3 className="text-gray-400 text-sm mb-1">Profit Margin</h3>
            <p className="text-2xl font-bold text-white">{(exec.profit_margin || 0).toFixed(1)}%</p>
            <p className="text-sm text-gray-500">Gross margin</p>
          </CardContent>
        </Card>

        {/* Cash Health */}
        <Card className="bg-gray-800/50 border-gray-700 backdrop-blur" data-testid="cash-health-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <BarChart3 className="w-8 h-8 text-purple-400" />
              {getHealthBadge(exec.cash_health)}
            </div>
            <h3 className="text-gray-400 text-sm mb-1">Cash Health</h3>
            <p className="text-2xl font-bold text-white">{exec.cash_health || 'N/A'}</p>
            <p className="text-sm text-gray-500">Variance monitoring</p>
          </CardContent>
        </Card>

        {/* Inventory Alerts */}
        <Card className="bg-gray-800/50 border-gray-700 backdrop-blur" data-testid="inventory-alerts-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <Package className="w-8 h-8 text-orange-400" />
              {exec.inventory_alerts > 10 && <AlertTriangle className="w-5 h-5 text-yellow-500" />}
            </div>
            <h3 className="text-gray-400 text-sm mb-1">Inventory Alerts</h3>
            <p className="text-2xl font-bold text-white">{exec.inventory_alerts || 0}</p>
            <p className="text-sm text-gray-500">Produk perlu restock</p>
          </CardContent>
        </Card>
      </div>

      {/* AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Sales Insight */}
        <Card className="bg-gray-800/50 border-gray-700" data-testid="sales-insight-card">
          <CardHeader className="border-b border-gray-700">
            <CardTitle className="flex items-center gap-2 text-white">
              <Lightbulb className="w-5 h-5 text-yellow-400" />
              Sales AI Insight
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <p className="text-gray-300">{insights.sales || 'Tidak ada data penjualan'}</p>
            {salesData?.dead_stock && (
              <div className="mt-4 p-4 bg-gray-700/50 rounded-lg">
                <h4 className="text-sm font-medium text-gray-400 mb-2">Dead Stock Alert</h4>
                <p className="text-white">
                  {salesData.dead_stock.dead_stock_count || 0} produk tanpa penjualan
                </p>
                <p className="text-sm text-gray-400">
                  Nilai: {formatCurrency(salesData.dead_stock.total_stuck_value)}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Profitability Insight */}
        <Card className="bg-gray-800/50 border-gray-700" data-testid="profit-insight-card">
          <CardHeader className="border-b border-gray-700">
            <CardTitle className="flex items-center gap-2 text-white">
              <Target className="w-5 h-5 text-green-400" />
              Profitability AI Insight
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <p className="text-gray-300">{insights.profitability || 'Tidak ada data profitabilitas'}</p>
          </CardContent>
        </Card>

        {/* Inventory Insight */}
        <Card className="bg-gray-800/50 border-gray-700" data-testid="inventory-insight-card">
          <CardHeader className="border-b border-gray-700">
            <CardTitle className="flex items-center gap-2 text-white">
              <Package className="w-5 h-5 text-orange-400" />
              Inventory AI Insight
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <p className="text-gray-300">{insights.inventory || 'Tidak ada rekomendasi inventory'}</p>
            {inventoryData?.restock_recommendations && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-400 mb-2">Top Restock Priority</h4>
                <div className="space-y-2">
                  {inventoryData.restock_recommendations.recommendations?.slice(0, 3).map((r, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <span className="text-white truncate max-w-[200px]">{r.product_name}</span>
                      <Badge className={r.urgency === 'HIGH' ? 'bg-red-600' : r.urgency === 'MEDIUM' ? 'bg-yellow-600' : 'bg-green-600'}>
                        {r.urgency}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Cash Insight */}
        <Card className="bg-gray-800/50 border-gray-700" data-testid="cash-insight-card">
          <CardHeader className="border-b border-gray-700">
            <CardTitle className="flex items-center gap-2 text-white">
              <DollarSign className="w-5 h-5 text-blue-400" />
              Cash AI Insight
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <p className="text-gray-300">{insights.cash || 'Tidak ada anomali kas'}</p>
          </CardContent>
        </Card>
      </div>

      {/* Risk Alerts */}
      {data?.risk_alerts?.filter(r => r).length > 0 && (
        <Card className="bg-red-900/30 border-red-700 mb-8" data-testid="risk-alerts-card">
          <CardHeader className="border-b border-red-700">
            <CardTitle className="flex items-center gap-2 text-red-400">
              <AlertTriangle className="w-5 h-5" />
              Risk Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-3">
              {data.risk_alerts.filter(r => r).map((alert, idx) => (
                <div key={idx} className="flex items-center gap-3 text-white">
                  <Badge className="bg-red-600">{alert.type?.toUpperCase()}</Badge>
                  <span>{alert.message}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Footer */}
      <div className="text-center text-gray-500 text-sm">
        <p>AI Business Engine - Mode: READ ONLY</p>
        <p>AI tidak melakukan perubahan data. Hanya menganalisis dan memberikan rekomendasi.</p>
        <p className="mt-2">Generated at: {data?.generated_at || new Date().toISOString()}</p>
      </div>
    </div>
  );
};

export default CEODashboardAI;
