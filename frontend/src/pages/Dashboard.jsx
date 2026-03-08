import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  TrendingUp, DollarSign, ShoppingCart, Users, Package, 
  AlertTriangle, Building2, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { toast } from 'sonner';

const Dashboard = () => {
  const { api, user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [salesTrend, setSalesTrend] = useState([]);

  useEffect(() => {
    loadDashboard();
    loadSalesTrend();
  }, []);

  const loadDashboard = async () => {
    try {
      const endpoint = user?.role === 'owner' || user?.role === 'admin' 
        ? '/api/dashboard/owner' 
        : '/api/dashboard/branch';
      
      const res = await api(endpoint);
      if (res.ok) {
        setData(await res.json());
      }
    } catch (err) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadSalesTrend = async () => {
    try {
      const res = await api('/api/dashboard/sales-trend?days=7');
      if (res.ok) {
        setSalesTrend((await res.json()).data || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  const isOwner = user?.role === 'owner' || user?.role === 'admin';
  const summary = isOwner ? data?.summary : data?.today;
  const branchName = isOwner ? 'All Branches' : data?.branch?.name;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Dashboard</h1>
          <p className="text-gray-400">{branchName} • {new Date().toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Today's Sales" value={`Rp ${(summary?.today_sales || summary?.sales || 0).toLocaleString()}`} icon={DollarSign} trend={12} color="green" />
        <StatCard title="Today's Profit" value={`Rp ${(summary?.today_profit || summary?.profit || 0).toLocaleString()}`} icon={TrendingUp} trend={8} color="amber" />
        <StatCard title="Transactions" value={summary?.today_transactions || summary?.transactions || 0} icon={ShoppingCart} trend={5} color="blue" />
        <StatCard title={isOwner ? "Cash Balance" : "Branch Cash"} value={`Rp ${(summary?.total_cash_balance || data?.branch?.cash_balance || 0).toLocaleString()}`} icon={Building2} color="purple" />
      </div>

      {isOwner && data?.counts && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MiniStatCard title="Total Branches" value={data.counts.branches} icon={Building2} />
          <MiniStatCard title="Total Products" value={data.counts.products} icon={Package} />
          <MiniStatCard title="Total Customers" value={data.counts.customers} icon={Users} />
          <MiniStatCard title="Total Employees" value={data.counts.employees} icon={Users} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4 text-amber-100">Sales Trend (7 Days)</h2>
          <div className="h-48 flex items-end gap-2">
            {salesTrend.map((day, idx) => {
              const maxSales = Math.max(...salesTrend.map(d => d.sales || 0), 1);
              const height = ((day.sales || 0) / maxSales) * 100;
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                  <div className="w-full bg-gradient-to-t from-red-600 to-amber-500 rounded-t" style={{ height: `${Math.max(height, 5)}%` }} />
                  <span className="text-xs text-gray-400">{day.date?.slice(5)}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4 text-amber-100">Best Selling Today</h2>
          <div className="space-y-3">
            {(data?.best_selling || []).slice(0, 5).map((product, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 bg-amber-600/20 text-amber-400 rounded-full flex items-center justify-center text-sm font-bold">{idx + 1}</span>
                  <div>
                    <div className="font-medium">{product.product_name}</div>
                    <div className="text-sm text-gray-400">{product.quantity_sold} sold</div>
                  </div>
                </div>
                <span className="text-amber-400 font-semibold">Rp {product.revenue?.toLocaleString()}</span>
              </div>
            ))}
            {(!data?.best_selling || data.best_selling.length === 0) && <p className="text-gray-400 text-center py-4">No sales today</p>}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {isOwner && data?.sales_by_branch && (
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 text-amber-100">Branch Performance</h2>
            <div className="space-y-3">
              {data.sales_by_branch.slice(0, 5).map((branch, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{branch.branch_name}</div>
                    <div className="text-sm text-gray-400">{branch.transactions} transactions</div>
                  </div>
                  <div className="text-right">
                    <div className="text-amber-400 font-semibold">Rp {branch.sales?.toLocaleString()}</div>
                    <div className="text-sm text-green-400">+Rp {branch.profit?.toLocaleString()}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            <h2 className="text-lg font-semibold text-amber-100">Low Stock Alerts</h2>
          </div>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {(data?.low_stock_alerts || data?.low_stock || []).slice(0, 10).map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-red-900/10 rounded-lg">
                <div>
                  <div className="font-medium">{item.product_name}</div>
                  <div className="text-sm text-gray-400">{item.branch_name && `${item.branch_name} • `}Min: {item.min_stock}</div>
                </div>
                <span className="text-red-400 font-bold">{item.quantity} left</span>
              </div>
            ))}
            {(!data?.low_stock_alerts?.length && !data?.low_stock?.length) && <p className="text-gray-400 text-center py-4">All stock levels OK</p>}
          </div>
        </div>
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
