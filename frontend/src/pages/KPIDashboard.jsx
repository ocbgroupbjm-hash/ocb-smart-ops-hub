import React, { useState, useEffect, useCallback } from 'react';
import { 
  BarChart3, TrendingUp, TrendingDown, Building2, Users, Package, 
  DollarSign, CreditCard, AlertTriangle, RefreshCw, Calendar,
  ArrowUp, ArrowDown, Wallet, Target, Award, ShoppingCart, Truck, Clock
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

import { getApiUrl } from '../utils/apiConfig';
const API_URL = getApiUrl();

// Format helpers
const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatPercent = (num) => `${(num || 0).toFixed(1)}%`;

// KPI Card Component
const KPICard = ({ title, value, format, trend, alert, target, icon: Icon, color = "amber" }) => {
  const colors = {
    amber: "from-amber-900/30 to-amber-800/10 border-amber-700/30",
    green: "from-green-900/30 to-green-800/10 border-green-700/30",
    blue: "from-blue-900/30 to-blue-800/10 border-blue-700/30",
    red: "from-red-900/30 to-red-800/10 border-red-700/30",
    purple: "from-purple-900/30 to-purple-800/10 border-purple-700/30"
  };
  
  const iconColors = {
    amber: "bg-amber-500/20 text-amber-400",
    green: "bg-green-500/20 text-green-400",
    blue: "bg-blue-500/20 text-blue-400",
    red: "bg-red-500/20 text-red-400",
    purple: "bg-purple-500/20 text-purple-400"
  };
  
  const formatValue = (val, fmt) => {
    if (fmt === 'currency') return formatRupiah(val);
    if (fmt === 'percent') return formatPercent(val);
    return val?.toLocaleString() || '0';
  };
  
  return (
    <div className={`bg-gradient-to-br ${colors[color]} border rounded-xl p-4 ${alert ? 'ring-2 ring-red-500/50' : ''}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-400 mb-1">{title}</p>
          <p className="text-xl font-bold text-amber-100">{formatValue(value, format)}</p>
          {target && format === 'percent' && (
            <p className="text-xs text-gray-500 mt-1">Target: {formatRupiah(target)}</p>
          )}
        </div>
        {Icon && (
          <div className={`h-10 w-10 rounded-lg ${iconColors[color]} flex items-center justify-center`}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
      {alert && (
        <div className="mt-2 flex items-center gap-1 text-xs text-red-400">
          <AlertTriangle className="h-3 w-3" />
          Requires attention
        </div>
      )}
    </div>
  );
};

// Branch Performance Card
const BranchCard = ({ branch }) => {
  const statusColors = {
    achieved: 'border-green-500/50 bg-green-500/5',
    on_track: 'border-amber-500/50 bg-amber-500/5',
    behind: 'border-red-500/50 bg-red-500/5'
  };
  
  return (
    <div className={`border rounded-xl p-4 ${statusColors[branch.status]}`} data-testid={`branch-kpi-${branch.branch_id}`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-amber-100 font-medium">{branch.branch_name}</h4>
          <p className="text-xs text-gray-500">{branch.branch_code}</p>
        </div>
        <span className={`px-2 py-1 text-xs rounded ${
          branch.status === 'achieved' ? 'bg-green-500/20 text-green-300' :
          branch.status === 'on_track' ? 'bg-amber-500/20 text-amber-300' :
          'bg-red-500/20 text-red-300'
        }`}>
          {branch.target.achievement_percent}%
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span className="text-gray-500 text-xs">Sales</span>
          <p className="text-green-400 font-medium">{formatRupiah(branch.sales.total)}</p>
        </div>
        <div>
          <span className="text-gray-500 text-xs">Target</span>
          <p className="text-gray-300">{formatRupiah(branch.target.value)}</p>
        </div>
        <div>
          <span className="text-gray-500 text-xs">Transactions</span>
          <p className="text-gray-300">{branch.sales.transaction_count}</p>
        </div>
        <div>
          <span className="text-gray-500 text-xs">Net Discrepancy</span>
          <p className={branch.cash_control.net_discrepancy < 0 ? 'text-red-400' : 'text-green-400'}>
            {formatRupiah(branch.cash_control.net_discrepancy)}
          </p>
        </div>
      </div>
    </div>
  );
};

// Sales Ranking Card
const SalesRankingCard = ({ salesman }) => (
  <div className="flex items-center gap-4 p-3 bg-black/20 rounded-lg" data-testid={`sales-kpi-${salesman.salesman_id}`}>
    <span className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold ${
      salesman.rank === 1 ? 'bg-amber-500/30 text-amber-300' :
      salesman.rank === 2 ? 'bg-gray-400/30 text-gray-300' :
      salesman.rank === 3 ? 'bg-orange-500/30 text-orange-300' :
      'bg-gray-600/30 text-gray-400'
    }`}>
      {salesman.rank}
    </span>
    <div className="flex-1">
      <p className="text-amber-100 font-medium">{salesman.salesman_name}</p>
      <p className="text-xs text-gray-500">{salesman.transaction_count} transactions</p>
    </div>
    <div className="text-right">
      <p className="text-green-400 font-medium">{formatRupiah(salesman.actual_sales)}</p>
      <p className={`text-xs ${
        salesman.achievement_percent >= 100 ? 'text-green-400' :
        salesman.achievement_percent >= 80 ? 'text-amber-400' :
        'text-red-400'
      }`}>
        {salesman.achievement_percent}%
      </p>
    </div>
  </div>
);

// Inventory Alert Card
const InventoryAlertCard = ({ item, type }) => (
  <div className="flex items-center gap-3 p-2 bg-black/20 rounded-lg text-sm">
    <Package className={`h-4 w-4 ${
      type === 'dead' ? 'text-red-400' :
      type === 'slow' ? 'text-amber-400' :
      'text-blue-400'
    }`} />
    <div className="flex-1 min-w-0">
      <p className="text-gray-300 truncate">{item.product_name}</p>
      <p className="text-xs text-gray-500">{item.product_code}</p>
    </div>
    <div className="text-right">
      <p className="text-gray-300">{item.current_stock} pcs</p>
      {item.days_no_sale && (
        <p className="text-xs text-red-400">{item.days_no_sale} days</p>
      )}
    </div>
  </div>
);

const KPIDashboard = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [period, setPeriod] = useState('month');
  
  // Data states
  const [dashboard, setDashboard] = useState(null);
  const [branchKPI, setBranchKPI] = useState(null);
  const [salesKPI, setSalesKPI] = useState(null);
  const [inventoryKPI, setInventoryKPI] = useState(null);
  const [financeKPI, setFinanceKPI] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      const [dashRes, branchRes, salesRes, invRes, finRes] = await Promise.all([
        fetch(`${API_URL}/api/kpi/dashboard?period=${period}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/kpi/branch/overview?period=${period}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/kpi/sales/overview?period=${period}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/kpi/inventory/overview`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/kpi/finance/overview?period=${period}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      
      const [dashData, branchData, salesData, invData, finData] = await Promise.all([
        dashRes.json(),
        branchRes.json(),
        salesRes.json(),
        invRes.json(),
        finRes.json()
      ]);
      
      setDashboard(dashData);
      setBranchKPI(branchData);
      setSalesKPI(salesData);
      setInventoryKPI(invData);
      setFinanceKPI(finData);
      
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, period]);

  useEffect(() => {
    if (token) fetchData();
  }, [token, fetchData]);

  const getCardIcon = (category) => {
    const icons = {
      sales: ShoppingCart,
      branch: Building2,
      inventory: Package,
      finance: DollarSign
    };
    return icons[category] || BarChart3;
  };

  const getCardColor = (category, alert) => {
    if (alert) return 'red';
    const colors = {
      sales: 'green',
      branch: 'blue',
      inventory: 'purple',
      finance: 'amber'
    };
    return colors[category] || 'amber';
  };

  return (
    <div className="space-y-6" data-testid="kpi-dashboard-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">KPI Dashboard</h1>
          <p className="text-gray-400 text-sm mt-1">Key Performance Indicators</p>
        </div>
        <div className="flex gap-2 items-center">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100"
            data-testid="period-select"
          >
            <option value="today">Hari Ini</option>
            <option value="week">Minggu Ini</option>
            <option value="month">Bulan Ini</option>
            <option value="quarter">Kuartal Ini</option>
            <option value="year">Tahun Ini</option>
          </select>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-red-900/30 hover:bg-red-900/50 text-amber-100 rounded-lg"
            data-testid="refresh-btn"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        {[
          { id: 'overview', label: 'Overview', icon: BarChart3 },
          { id: 'branch', label: 'Branch', icon: Building2 },
          { id: 'sales', label: 'Sales', icon: Users },
          { id: 'inventory', label: 'Inventory', icon: Package },
          { id: 'finance', label: 'Finance', icon: DollarSign }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors ${
              activeTab === tab.id 
                ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
                : 'text-gray-400 hover:text-amber-100'
            }`}
            data-testid={`tab-${tab.id}`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="h-8 w-8 text-amber-500 animate-spin" />
        </div>
      ) : (
        <>
          {/* Overview Tab */}
          {activeTab === 'overview' && dashboard && (
            <div className="space-y-6">
              {/* KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {dashboard.kpi_cards?.map((card, idx) => (
                  <KPICard
                    key={idx}
                    title={card.title}
                    value={card.value}
                    format={card.format}
                    target={card.target}
                    alert={card.alert}
                    icon={getCardIcon(card.category)}
                    color={getCardColor(card.category, card.alert)}
                  />
                ))}
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-6">
                {/* Top Branches */}
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
                  <h3 className="text-amber-100 font-medium mb-4 flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-blue-400" />
                    Top Branches
                  </h3>
                  <div className="space-y-2">
                    {branchKPI?.branches?.slice(0, 5).map((b, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-black/20 rounded">
                        <span className="text-gray-300">{b.branch_name}</span>
                        <span className="text-green-400 font-medium">{formatRupiah(b.sales.total)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Top Salesmen */}
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
                  <h3 className="text-amber-100 font-medium mb-4 flex items-center gap-2">
                    <Award className="h-5 w-5 text-amber-400" />
                    Top Salesmen
                  </h3>
                  <div className="space-y-2">
                    {salesKPI?.ranking?.slice(0, 5).map((s, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-black/20 rounded">
                        <div className="flex items-center gap-2">
                          <span className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold ${
                            idx === 0 ? 'bg-amber-500/30 text-amber-300' :
                            idx === 1 ? 'bg-gray-400/30 text-gray-300' :
                            'bg-gray-600/30 text-gray-400'
                          }`}>
                            {idx + 1}
                          </span>
                          <span className="text-gray-300">{s.salesman_name}</span>
                        </div>
                        <span className="text-green-400">{s.achievement_percent}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Branch Tab */}
          {activeTab === 'branch' && branchKPI && (
            <div className="space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-4 gap-4">
                <KPICard title="Total Branches" value={branchKPI.summary.total_branches} format="number" icon={Building2} color="blue" />
                <KPICard title="Total Sales" value={branchKPI.summary.total_sales} format="currency" icon={DollarSign} color="green" />
                <KPICard title="Overall Achievement" value={branchKPI.summary.overall_achievement} format="percent" icon={Target} color="amber" />
                <KPICard title="Behind Target" value={branchKPI.summary.behind_count} format="number" icon={AlertTriangle} color="red" alert={branchKPI.summary.behind_count > 0} />
              </div>

              {/* Branch Cards */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {branchKPI.branches?.map((branch, idx) => (
                  <BranchCard key={idx} branch={branch} />
                ))}
              </div>
            </div>
          )}

          {/* Sales Tab */}
          {activeTab === 'sales' && salesKPI && (
            <div className="space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-4 gap-4">
                <KPICard title="Total Salesmen" value={salesKPI.summary.total_salesmen} format="number" icon={Users} color="blue" />
                <KPICard title="Total Sales" value={salesKPI.summary.total_sales} format="currency" icon={DollarSign} color="green" />
                <KPICard title="Total Commission" value={salesKPI.summary.total_commission} format="currency" icon={Wallet} color="purple" />
                <KPICard title="Achieved Target" value={salesKPI.summary.achieved_count} format="number" icon={Award} color="amber" />
              </div>

              {/* Ranking */}
              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
                <h3 className="text-amber-100 font-medium mb-4 flex items-center gap-2">
                  <Award className="h-5 w-5 text-amber-400" />
                  Sales Ranking
                </h3>
                <div className="space-y-2">
                  {salesKPI.ranking?.map((salesman, idx) => (
                    <SalesRankingCard key={idx} salesman={salesman} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Inventory Tab */}
          {activeTab === 'inventory' && inventoryKPI && (
            <div className="space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-4 gap-4">
                <KPICard title="Total Products" value={inventoryKPI.summary.total_products} format="number" icon={Package} color="blue" />
                <KPICard title="Stock Value" value={inventoryKPI.summary.total_stock_value} format="currency" icon={DollarSign} color="green" />
                <KPICard title="Low Stock" value={inventoryKPI.summary.low_stock_count} format="number" icon={AlertTriangle} color="amber" alert={inventoryKPI.summary.low_stock_count > 10} />
                <KPICard title="Dead Stock" value={inventoryKPI.summary.dead_stock_count} format="number" icon={Package} color="red" alert={inventoryKPI.summary.dead_stock_count > 5} />
              </div>

              {/* Alerts Grid */}
              <div className="grid grid-cols-3 gap-4">
                {/* Low Stock */}
                <div className="bg-[#1a1214] border border-amber-900/30 rounded-xl p-4">
                  <h4 className="text-amber-300 font-medium mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Low Stock ({inventoryKPI.summary.low_stock_count})
                  </h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {inventoryKPI.low_stock?.map((item, idx) => (
                      <InventoryAlertCard key={idx} item={item} type="low" />
                    ))}
                    {inventoryKPI.low_stock?.length === 0 && (
                      <p className="text-gray-500 text-sm">No low stock items</p>
                    )}
                  </div>
                </div>

                {/* Slow Moving */}
                <div className="bg-[#1a1214] border border-amber-900/30 rounded-xl p-4">
                  <h4 className="text-amber-300 font-medium mb-3 flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Slow Moving ({inventoryKPI.summary.slow_moving_count})
                  </h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {inventoryKPI.slow_moving?.map((item, idx) => (
                      <InventoryAlertCard key={idx} item={item} type="slow" />
                    ))}
                    {inventoryKPI.slow_moving?.length === 0 && (
                      <p className="text-gray-500 text-sm">No slow moving items</p>
                    )}
                  </div>
                </div>

                {/* Dead Stock */}
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
                  <h4 className="text-red-300 font-medium mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Dead Stock ({inventoryKPI.summary.dead_stock_count})
                  </h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {inventoryKPI.dead_stock?.map((item, idx) => (
                      <InventoryAlertCard key={idx} item={item} type="dead" />
                    ))}
                    {inventoryKPI.dead_stock?.length === 0 && (
                      <p className="text-gray-500 text-sm">No dead stock items</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Warehouse Stock */}
              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
                <h4 className="text-amber-100 font-medium mb-3">Stock by Warehouse</h4>
                <div className="grid grid-cols-4 gap-4">
                  {inventoryKPI.warehouse_stock?.map((wh, idx) => (
                    <div key={idx} className="p-3 bg-black/20 rounded-lg">
                      <p className="text-gray-300 font-medium">{wh.warehouse_name}</p>
                      <p className="text-green-400">{formatRupiah(wh.total_value)}</p>
                      <p className="text-xs text-gray-500">{wh.total_items} items</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Finance Tab */}
          {activeTab === 'finance' && financeKPI && (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-4 gap-4">
                <KPICard title="Revenue" value={financeKPI.profit_summary.revenue} format="currency" icon={TrendingUp} color="green" />
                <KPICard title="Gross Profit" value={financeKPI.profit_summary.gross_profit} format="currency" icon={DollarSign} color="amber" />
                <KPICard title="Total AR" value={financeKPI.ar_summary.total} format="currency" icon={CreditCard} color="blue" />
                <KPICard title="Total AP" value={financeKPI.ap_summary.total} format="currency" icon={Truck} color="purple" />
              </div>

              <div className="grid grid-cols-2 gap-6">
                {/* AR Aging */}
                <div className="bg-[#1a1214] border border-blue-900/30 rounded-xl p-4">
                  <h4 className="text-blue-300 font-medium mb-4 flex items-center gap-2">
                    <CreditCard className="h-5 w-5" />
                    AR Aging
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(financeKPI.ar_summary.aging || {}).map(([bucket, amount]) => (
                      <div key={bucket} className="flex justify-between items-center p-2 bg-black/20 rounded">
                        <span className="text-gray-400 capitalize">{bucket.replace('_', '-')} days</span>
                        <span className={`font-medium ${bucket === 'over_90' ? 'text-red-400' : 'text-gray-300'}`}>
                          {formatRupiah(amount)}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 pt-3 border-t border-blue-900/30">
                    <p className="text-xs text-gray-500">
                      Overdue: {financeKPI.ar_summary.overdue_percent}%
                    </p>
                  </div>
                </div>

                {/* AP Aging */}
                <div className="bg-[#1a1214] border border-purple-900/30 rounded-xl p-4">
                  <h4 className="text-purple-300 font-medium mb-4 flex items-center gap-2">
                    <Truck className="h-5 w-5" />
                    AP Aging
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(financeKPI.ap_summary.aging || {}).map(([bucket, amount]) => (
                      <div key={bucket} className="flex justify-between items-center p-2 bg-black/20 rounded">
                        <span className="text-gray-400 capitalize">{bucket.replace('_', '-')} days</span>
                        <span className={`font-medium ${bucket === 'over_90' ? 'text-red-400' : 'text-gray-300'}`}>
                          {formatRupiah(amount)}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 pt-3 border-t border-purple-900/30">
                    <p className="text-xs text-gray-500">
                      Overdue: {financeKPI.ap_summary.overdue_percent}%
                    </p>
                  </div>
                </div>
              </div>

              {/* Branch Profitability */}
              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
                <h4 className="text-amber-100 font-medium mb-4">Branch Profitability</h4>
                <div className="space-y-2">
                  {financeKPI.branch_profitability?.map((branch, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-black/20 rounded-lg">
                      <span className="text-gray-300">{branch.branch_name}</span>
                      <div className="flex gap-6">
                        <div className="text-right">
                          <p className="text-xs text-gray-500">Revenue</p>
                          <p className="text-green-400">{formatRupiah(branch.revenue)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-gray-500">Est. Profit</p>
                          <p className="text-amber-100">{formatRupiah(branch.estimated_profit)}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default KPIDashboard;
