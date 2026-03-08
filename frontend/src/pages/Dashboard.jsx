import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { 
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, Users, Package, 
  AlertTriangle, Building2, ArrowUpRight, ArrowDownRight, RefreshCw, Brain, Store, ShoppingBag,
  Sparkles, MessageSquare, ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';

const Dashboard = () => {
  const { api, user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [salesTrend, setSalesTrend] = useState([]);
  const [aiInsights, setAiInsights] = useState([]);

  useEffect(() => {
    loadDashboard();
    loadSalesTrend();
    loadAIInsights();
  }, []);

  const loadDashboard = async () => {
    try {
      const endpoint = user?.role === 'owner' || user?.role === 'admin' 
        ? '/api/dashboard/owner' 
        : '/api/dashboard/branch';
      
      const res = await api(endpoint);
      if (res.ok) setData(await res.json());
    } catch (err) {
      toast.error('Gagal memuat dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadSalesTrend = async () => {
    try {
      const res = await api('/api/dashboard/sales-trend?days=7');
      if (res.ok) setSalesTrend((await res.json()).data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const loadAIInsights = async () => {
    try {
      const res = await api('/api/ai-bisnis/dashboard-widget');
      if (res.ok) {
        const result = await res.json();
        setAiInsights(result.insights || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
  const formatDate = () => new Date().toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-red-400" />
      </div>
    );
  }

  const isOwner = user?.role === 'owner' || user?.role === 'admin';
  const summary = isOwner ? data?.summary : data?.today;
  const branchName = isOwner ? 'Semua Cabang' : data?.branch?.name;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Dashboard</h1>
          <p className="text-gray-400">{branchName} • {formatDate()}</p>
        </div>
        <button onClick={() => { loadDashboard(); loadSalesTrend(); loadAIInsights(); }} className="p-2 hover:bg-red-900/20 rounded-lg">
          <RefreshCw className="h-5 w-5 text-gray-400" />
        </button>
      </div>

      {/* AI Insights Widget */}
      {aiInsights.length > 0 && (
        <div className="bg-gradient-to-r from-purple-900/20 via-blue-900/20 to-purple-900/20 border border-purple-700/30 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-purple-400" />
              <span className="font-semibold text-purple-300">AI Insights</span>
            </div>
            <button 
              onClick={() => navigate('/hallo-ai')}
              className="flex items-center gap-1 text-sm text-purple-400 hover:text-purple-300"
            >
              <Sparkles className="h-4 w-4" /> Buka Hallo AI
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
            {aiInsights.map((insight, idx) => {
              const iconMap = { 
                trending_up: TrendingUp, 
                trending_down: TrendingDown, 
                warning: AlertTriangle, 
                store: Store, 
                alert: AlertTriangle,
                shopping_cart: ShoppingBag
              };
              const colorMap = {
                green: 'text-green-400 bg-green-900/20 border-green-700/30',
                red: 'text-red-400 bg-red-900/20 border-red-700/30',
                amber: 'text-amber-400 bg-amber-900/20 border-amber-700/30',
                blue: 'text-blue-400 bg-blue-900/20 border-blue-700/30',
                purple: 'text-purple-400 bg-purple-900/20 border-purple-700/30'
              };
              const Icon = iconMap[insight.icon] || TrendingUp;
              const colorClass = colorMap[insight.color] || colorMap.blue;
              
              return (
                <div key={idx} className={`p-3 rounded-lg border ${colorClass}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className="h-4 w-4" />
                    <span className="text-xs font-medium">{insight.title}</span>
                  </div>
                  <div className="text-lg font-bold">{insight.value}</div>
                  <div className="text-xs opacity-70">{insight.description}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Kartu Statistik */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Penjualan Hari Ini" value={formatRupiah(summary?.today_sales || summary?.sales)} icon={DollarSign} trend={12} color="green" />
        <StatCard title="Laba Hari Ini" value={formatRupiah(summary?.today_profit || summary?.profit)} icon={TrendingUp} trend={8} color="amber" />
        <StatCard title="Total Transaksi" value={summary?.today_transactions || summary?.transactions || 0} icon={ShoppingCart} trend={5} color="blue" />
        <StatCard title={isOwner ? "Total Saldo Kas" : "Saldo Kas Cabang"} value={formatRupiah(summary?.total_cash_balance || data?.branch?.cash_balance)} icon={Building2} color="purple" />
      </div>

      {/* Statistik Mini */}
      {isOwner && data?.counts && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MiniStatCard title="Total Cabang" value={data.counts.branches} icon={Building2} />
          <MiniStatCard title="Total Produk" value={data.counts.products} icon={Package} />
          <MiniStatCard title="Total Pelanggan" value={data.counts.customers} icon={Users} />
          <MiniStatCard title="Total Karyawan" value={data.counts.employees} icon={Users} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Grafik Penjualan */}
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4 text-amber-100">Trend Penjualan (7 Hari)</h2>
          <div className="h-48 flex items-end gap-2">
            {salesTrend.length > 0 ? salesTrend.map((day, idx) => {
              const maxSales = Math.max(...salesTrend.map(d => d.sales || 0), 1);
              const height = ((day.sales || 0) / maxSales) * 100;
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                  <div className="text-xs text-amber-400 font-semibold">{formatRupiah(day.sales).replace('Rp ', '')}</div>
                  <div className="w-full bg-gradient-to-t from-red-600 to-amber-500 rounded-t transition-all" style={{ height: `${Math.max(height, 5)}%` }} />
                  <span className="text-xs text-gray-400">{day.date?.slice(8, 10)}/{day.date?.slice(5, 7)}</span>
                </div>
              );
            }) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">Belum ada data penjualan</div>
            )}
          </div>
        </div>

        {/* Produk Terlaris */}
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4 text-amber-100">Produk Terlaris Hari Ini</h2>
          <div className="space-y-3">
            {(data?.best_selling || []).slice(0, 5).map((product, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 bg-amber-600/20 text-amber-400 rounded-full flex items-center justify-center text-sm font-bold">{idx + 1}</span>
                  <div>
                    <div className="font-medium">{product.product_name}</div>
                    <div className="text-sm text-gray-400">{product.quantity_sold} terjual</div>
                  </div>
                </div>
                <span className="text-amber-400 font-semibold">{formatRupiah(product.revenue)}</span>
              </div>
            ))}
            {(!data?.best_selling || data.best_selling.length === 0) && <p className="text-gray-400 text-center py-4">Belum ada penjualan hari ini</p>}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performa Cabang (Owner Only) */}
        {isOwner && data?.sales_by_branch && data.sales_by_branch.length > 0 && (
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 text-amber-100">Performa Cabang</h2>
            <div className="space-y-3">
              {data.sales_by_branch.slice(0, 5).map((branch, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-red-900/10 rounded-lg">
                  <div>
                    <div className="font-medium">{branch.branch_name}</div>
                    <div className="text-sm text-gray-400">{branch.transactions} transaksi</div>
                  </div>
                  <div className="text-right">
                    <div className="text-amber-400 font-semibold">{formatRupiah(branch.sales)}</div>
                    <div className="text-sm text-green-400">+{formatRupiah(branch.profit)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Peringatan Stok Menipis */}
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            <h2 className="text-lg font-semibold text-amber-100">Peringatan Stok Menipis</h2>
          </div>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {(data?.low_stock_alerts || data?.low_stock || []).slice(0, 10).map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-red-900/10 rounded-lg">
                <div>
                  <div className="font-medium">{item.product_name}</div>
                  <div className="text-sm text-gray-400">{item.branch_name && `${item.branch_name} • `}Min: {item.min_stock}</div>
                </div>
                <span className="text-red-400 font-bold">{item.quantity} sisa</span>
              </div>
            ))}
            {(!data?.low_stock_alerts?.length && !data?.low_stock?.length) && <p className="text-gray-400 text-center py-4">Semua stok dalam kondisi baik</p>}
          </div>
        </div>

        {/* Transaksi Terbaru (Branch View) */}
        {!isOwner && data?.recent_transactions && (
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 text-amber-100">Transaksi Terbaru</h2>
            <div className="space-y-3">
              {data.recent_transactions.slice(0, 5).map((tx, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-red-900/10 rounded-lg">
                  <div>
                    <div className="font-medium">{tx.invoice_number}</div>
                    <div className="text-sm text-gray-400">{tx.customer_name || 'Umum'} • {new Date(tx.created_at).toLocaleTimeString('id-ID')}</div>
                  </div>
                  <span className={`font-semibold ${tx.status === 'completed' ? 'text-green-400' : 'text-amber-400'}`}>
                    {formatRupiah(tx.total)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon: Icon, trend, color }) => {
  const colors = { green: 'from-green-600/20 to-green-900/10 border-green-800/30', amber: 'from-amber-600/20 to-amber-900/10 border-amber-800/30', blue: 'from-blue-600/20 to-blue-900/10 border-blue-800/30', purple: 'from-purple-600/20 to-purple-900/10 border-purple-800/30' };
  const iconColors = { green: 'text-green-400', amber: 'text-amber-400', blue: 'text-blue-400', purple: 'text-purple-400' };

  return (
    <div className={`bg-gradient-to-br ${colors[color]} border rounded-xl p-5`}>
      <div className="flex justify-between items-start mb-3">
        <Icon className={`h-8 w-8 ${iconColors[color]}`} />
        {trend !== undefined && (
          <span className={`flex items-center text-sm ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trend >= 0 ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
            {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-gray-400">{title}</div>
    </div>
  );
};

const MiniStatCard = ({ title, value, icon: Icon }) => (
  <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 flex items-center gap-3">
    <Icon className="h-8 w-8 text-red-400" />
    <div>
      <div className="text-xl font-bold">{value}</div>
      <div className="text-sm text-gray-400">{title}</div>
    </div>
  </div>
);

export default Dashboard;
