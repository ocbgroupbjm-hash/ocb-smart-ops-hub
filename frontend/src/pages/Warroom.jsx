import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  Building2, TrendingUp, TrendingDown, DollarSign, ShoppingCart, 
  AlertTriangle, Users, MessageSquare, Package, RefreshCw,
  BarChart3, Activity, MapPin
} from 'lucide-react';
import { toast } from 'sonner';

const Warroom = () => {
  const { api } = useAuth();
  const [snapshot, setSnapshot] = useState(null);
  const [branchPerformance, setBranchPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadData = async () => {
    try {
      const [snapRes, branchRes] = await Promise.all([
        api('/api/warroom/snapshot'),
        api('/api/warroom/branches/performance?period=today')
      ]);

      if (snapRes.ok) {
        setSnapshot(await snapRes.json());
      }
      if (branchRes.ok) {
        setBranchPerformance(await branchRes.json());
      }
    } catch (err) {
      console.error('Failed to load warroom data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    
    // Auto refresh every 30 seconds
    let interval;
    if (autoRefresh) {
      interval = setInterval(loadData, 30000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value || 0);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0608]">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 text-amber-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Memuat Warroom...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0608] text-white p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">🏢 WARROOM OCB GROUP</h1>
          <p className="text-gray-400 text-sm">Real-time Monitoring Seluruh Cabang</p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input 
              type="checkbox" 
              checked={autoRefresh} 
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            Auto Refresh (30s)
          </label>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Today Revenue */}
        <div className="bg-gradient-to-br from-green-900/40 to-green-800/20 border border-green-700/30 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-400 text-sm">Revenue Hari Ini</p>
              <p className="text-2xl font-bold text-white">{formatCurrency(snapshot?.today_revenue)}</p>
              <div className={`flex items-center gap-1 text-sm ${snapshot?.revenue_change_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {snapshot?.revenue_change_percent >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                {snapshot?.revenue_change_percent?.toFixed(1)}% vs kemarin
              </div>
            </div>
            <DollarSign className="h-10 w-10 text-green-500/50" />
          </div>
        </div>

        {/* Transactions */}
        <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 border border-blue-700/30 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-400 text-sm">Transaksi Hari Ini</p>
              <p className="text-2xl font-bold text-white">{snapshot?.today_transactions || 0}</p>
              <p className="text-sm text-gray-400">
                Avg: {formatCurrency(snapshot?.today_transactions > 0 ? snapshot?.today_revenue / snapshot?.today_transactions : 0)}
              </p>
            </div>
            <ShoppingCart className="h-10 w-10 text-blue-500/50" />
          </div>
        </div>

        {/* Active Branches */}
        <div className="bg-gradient-to-br from-purple-900/40 to-purple-800/20 border border-purple-700/30 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-400 text-sm">Cabang Aktif</p>
              <p className="text-2xl font-bold text-white">{snapshot?.active_branches || 0} / {snapshot?.total_branches || 0}</p>
              <p className="text-sm text-gray-400">Seluruh Indonesia</p>
            </div>
            <Building2 className="h-10 w-10 text-purple-500/50" />
          </div>
        </div>

        {/* Alerts */}
        <div className="bg-gradient-to-br from-red-900/40 to-red-800/20 border border-red-700/30 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-400 text-sm">Stock Alerts</p>
              <p className="text-2xl font-bold text-white">{snapshot?.critical_stock_alerts || 0}</p>
              <p className="text-sm text-gray-400">Perlu perhatian</p>
            </div>
            <AlertTriangle className="h-10 w-10 text-red-500/50" />
          </div>
        </div>
      </div>

      {/* Second Row - Active Operations */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <MessageSquare className="h-5 w-5 text-amber-500" />
            <span className="text-amber-100 font-medium">Active Conversations</span>
          </div>
          <p className="text-3xl font-bold">{snapshot?.active_conversations || 0}</p>
          <p className="text-sm text-gray-400">AI sedang melayani pelanggan</p>
        </div>

        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <Package className="h-5 w-5 text-amber-500" />
            <span className="text-amber-100 font-medium">Pending Orders</span>
          </div>
          <p className="text-3xl font-bold">{snapshot?.pending_orders || 0}</p>
          <p className="text-sm text-gray-400">Menunggu diproses</p>
        </div>

        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <Activity className="h-5 w-5 text-amber-500" />
            <span className="text-amber-100 font-medium">Active Campaigns</span>
          </div>
          <p className="text-3xl font-bold">{snapshot?.active_campaigns || 0}</p>
          <p className="text-sm text-gray-400">Marketing campaign berjalan</p>
        </div>
      </div>

      {/* Branch Performance Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-amber-100 flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Performa Cabang Hari Ini
          </h2>
          <span className="text-sm text-gray-400">
            Total: {formatCurrency(branchPerformance?.total_revenue)}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm border-b border-red-900/20">
                <th className="pb-3 pr-4">Cabang</th>
                <th className="pb-3 pr-4">Kota</th>
                <th className="pb-3 pr-4 text-right">Revenue</th>
                <th className="pb-3 pr-4 text-right">Transaksi</th>
                <th className="pb-3 pr-4 text-right">Avg Trans</th>
                <th className="pb-3 text-right">Target</th>
              </tr>
            </thead>
            <tbody>
              {branchPerformance?.branches?.slice(0, 15).map((branch, idx) => (
                <tr key={branch.branch_id} className="border-b border-red-900/10 hover:bg-red-900/10">
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        idx < 3 ? 'bg-amber-600 text-white' : 'bg-gray-700 text-gray-300'
                      }`}>
                        {idx + 1}
                      </span>
                      <div>
                        <p className="font-medium text-white">{branch.branch_name}</p>
                        <p className="text-xs text-gray-500">{branch.branch_code}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 pr-4 text-gray-400">
                    <div className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {branch.city || '-'}
                    </div>
                  </td>
                  <td className="py-3 pr-4 text-right font-medium text-green-400">
                    {formatCurrency(branch.revenue)}
                  </td>
                  <td className="py-3 pr-4 text-right text-gray-300">
                    {branch.transactions}
                  </td>
                  <td className="py-3 pr-4 text-right text-gray-300">
                    {formatCurrency(branch.average_transaction)}
                  </td>
                  <td className="py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${
                            branch.achievement_percent >= 100 ? 'bg-green-500' :
                            branch.achievement_percent >= 50 ? 'bg-amber-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${Math.min(100, branch.achievement_percent || 0)}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400 w-12 text-right">
                        {branch.achievement_percent?.toFixed(0) || 0}%
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {branchPerformance?.branches?.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            Belum ada data transaksi hari ini
          </div>
        )}
      </div>

      {/* Top Branches Quick View */}
      {snapshot?.top_branches?.length > 0 && (
        <div className="mt-6 bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <h2 className="text-lg font-bold text-amber-100 mb-4">🏆 Top 5 Cabang Hari Ini</h2>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {snapshot.top_branches.map((branch, idx) => (
              <div key={branch.branch_id} className="bg-[#0a0608] rounded-lg p-3 border border-amber-600/20">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '🏅'}</span>
                  <span className="font-medium text-amber-100 text-sm truncate">{branch.branch_name}</span>
                </div>
                <p className="text-lg font-bold text-green-400">{formatCurrency(branch.revenue)}</p>
                <p className="text-xs text-gray-400">{branch.transactions} transaksi</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Warroom;
