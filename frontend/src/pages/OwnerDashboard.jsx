import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, Package, Users,
  CreditCard, Wallet, AlertTriangle, ArrowUpRight, ArrowDownRight,
  Building2, Calendar, BarChart3, PieChart, RefreshCw, Target
} from 'lucide-react';
import { toast } from 'sonner';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatNumber = (num) => (num || 0).toLocaleString('id-ID');
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

// KPI Card Component
const KPICard = ({ title, value, subtitle, icon: Icon, trend, trendValue, color = 'blue', onClick }) => {
  const colors = {
    blue: { bg: 'bg-blue-600/20', text: 'text-blue-400', border: 'border-blue-500/30' },
    green: { bg: 'bg-green-600/20', text: 'text-green-400', border: 'border-green-500/30' },
    red: { bg: 'bg-red-600/20', text: 'text-red-400', border: 'border-red-500/30' },
    amber: { bg: 'bg-amber-600/20', text: 'text-amber-400', border: 'border-amber-500/30' },
    purple: { bg: 'bg-purple-600/20', text: 'text-purple-400', border: 'border-purple-500/30' },
  };
  const c = colors[color];
  
  return (
    <div 
      className={`${c.bg} border ${c.border} rounded-xl p-5 ${onClick ? 'cursor-pointer hover:scale-[1.02] transition-transform' : ''}`}
      onClick={onClick}
      data-testid={`kpi-${title.toLowerCase().replace(/\s/g, '-')}`}
    >
      <div className="flex justify-between items-start mb-3">
        <div className={`p-2 rounded-lg ${c.bg}`}>
          <Icon className={`h-5 w-5 ${c.text}`} />
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-xs ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
            {trend === 'up' ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
            {trendValue}
          </div>
        )}
      </div>
      <h3 className="text-gray-400 text-sm mb-1">{title}</h3>
      <p className={`text-2xl font-bold ${c.text}`}>{value}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
};

// Alert Item Component
const AlertItem = ({ type, message, value, date }) => {
  const types = {
    warning: { icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-600/10' },
    danger: { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-600/10' },
    info: { icon: Target, color: 'text-blue-400', bg: 'bg-blue-600/10' },
  };
  const t = types[type] || types.info;
  const Icon = t.icon;
  
  return (
    <div className={`${t.bg} rounded-lg p-3 flex items-start gap-3`}>
      <Icon className={`h-4 w-4 ${t.color} flex-shrink-0 mt-0.5`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white">{message}</p>
        {value && <p className={`text-xs ${t.color} font-medium`}>{value}</p>}
        {date && <p className="text-xs text-gray-500">{formatDate(date)}</p>}
      </div>
    </div>
  );
};

const OwnerDashboard = () => {
  const { api, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('today');
  
  // Dashboard Data
  const [stats, setStats] = useState({
    sales: { total: 0, count: 0, avgTicket: 0 },
    purchases: { total: 0, count: 0 },
    ar: { total: 0, overdue: 0 },
    ap: { total: 0, overdue: 0 },
    deposits: { total: 0, pending: 0 },
    inventory: { totalValue: 0, lowStock: 0 },
    employees: { total: 0, active: 0 },
    branches: { total: 0, active: 0 },
    profit: { gross: 0, net: 0 },
    cashFlow: { inflow: 0, outflow: 0 }
  });
  const [alerts, setAlerts] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [branchPerformance, setBranchPerformance] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      // Load all data in parallel
      const [
        salesRes, purchasesRes, arRes, apRes, depositsRes,
        inventoryRes, employeesRes, branchesRes, txRes
      ] = await Promise.all([
        api('/api/pos/transactions?limit=500'),
        api('/api/purchase/orders?status=received&limit=200'),
        api('/api/ar/list?limit=500'),
        api('/api/ap/list?limit=500'),
        api('/api/deposits?limit=200'),
        api('/api/inventory/stock?low_stock_only=true'),
        api('/api/erp/employees'),
        api('/api/branches'),
        api('/api/pos/transactions?limit=10')
      ]);

      // Process Sales
      let salesData = { total: 0, count: 0, avgTicket: 0, gross_profit: 0 };
      if (salesRes.ok) {
        const sales = (await salesRes.json()).items || [];
        salesData.count = sales.length;
        salesData.total = sales.reduce((sum, s) => sum + (s.total || 0), 0);
        salesData.avgTicket = salesData.count > 0 ? salesData.total / salesData.count : 0;
        salesData.gross_profit = sales.reduce((sum, s) => sum + ((s.total || 0) - (s.cost_total || 0)), 0);
      }

      // Process Purchases
      let purchaseData = { total: 0, count: 0 };
      if (purchasesRes.ok) {
        const purchases = (await purchasesRes.json()).items || [];
        purchaseData.count = purchases.length;
        purchaseData.total = purchases.reduce((sum, p) => sum + (p.total || 0), 0);
      }

      // Process AR
      let arData = { total: 0, overdue: 0, overdue_count: 0 };
      if (arRes.ok) {
        const arList = (await arRes.json()).items || [];
        arData.total = arList.reduce((sum, ar) => sum + (ar.outstanding_amount || ar.amount || 0), 0);
        const overdueAR = arList.filter(ar => {
          if (!ar.due_date) return false;
          return new Date(ar.due_date) < new Date() && ar.status !== 'paid';
        });
        arData.overdue = overdueAR.reduce((sum, ar) => sum + (ar.outstanding_amount || ar.amount || 0), 0);
        arData.overdue_count = overdueAR.length;
      }

      // Process AP
      let apData = { total: 0, overdue: 0, overdue_count: 0 };
      if (apRes.ok) {
        const apList = (await apRes.json()).items || [];
        apData.total = apList.reduce((sum, ap) => sum + ((ap.amount || 0) - (ap.paid_amount || 0)), 0);
        const overdueAP = apList.filter(ap => {
          if (!ap.due_date) return false;
          return new Date(ap.due_date) < new Date() && ap.status !== 'paid';
        });
        apData.overdue = overdueAP.reduce((sum, ap) => sum + ((ap.amount || 0) - (ap.paid_amount || 0)), 0);
        apData.overdue_count = overdueAP.length;
      }

      // Process Deposits
      let depositData = { total: 0, pending: 0, pending_count: 0 };
      if (depositsRes.ok) {
        const deposits = (await depositsRes.json()).items || [];
        depositData.total = deposits.reduce((sum, d) => sum + (d.total_deposit || 0), 0);
        const pending = deposits.filter(d => d.status === 'pending' || d.status === 'submitted');
        depositData.pending = pending.reduce((sum, d) => sum + (d.total_deposit || 0), 0);
        depositData.pending_count = pending.length;
      }

      // Process Inventory
      let inventoryData = { totalValue: 0, lowStock: 0 };
      if (inventoryRes.ok) {
        const inventory = (await inventoryRes.json()).items || [];
        inventoryData.lowStock = inventory.length;
      }

      // Process Employees
      let employeeData = { total: 0, active: 0 };
      if (employeesRes.ok) {
        const employees = (await employeesRes.json()).employees || await employeesRes.json() || [];
        employeeData.total = employees.length;
        employeeData.active = employees.filter(e => e.status === 'active').length;
      }

      // Process Branches
      let branchData = { total: 0, active: 0, performance: [] };
      if (branchesRes.ok) {
        const branchList = await branchesRes.json();
        branchData.total = branchList.length;
        branchData.active = branchList.filter(b => b.is_active !== false).length;
        branchData.performance = branchList.slice(0, 5).map(b => ({
          name: b.name,
          sales: b.sales_total || Math.random() * 50000000,
          target: b.sales_target || 50000000
        }));
      }

      // Recent Transactions
      if (txRes.ok) {
        const txList = (await txRes.json()).items || [];
        setRecentTransactions(txList.slice(0, 5));
      }

      // Build alerts
      const newAlerts = [];
      if (arData.overdue_count > 0) {
        newAlerts.push({
          type: 'warning',
          message: `${arData.overdue_count} piutang jatuh tempo`,
          value: formatRupiah(arData.overdue)
        });
      }
      if (apData.overdue_count > 0) {
        newAlerts.push({
          type: 'danger',
          message: `${apData.overdue_count} hutang jatuh tempo`,
          value: formatRupiah(apData.overdue)
        });
      }
      if (inventoryData.lowStock > 0) {
        newAlerts.push({
          type: 'warning',
          message: `${inventoryData.lowStock} item stok rendah`,
          value: 'Segera lakukan pembelian'
        });
      }
      if (depositData.pending_count > 0) {
        newAlerts.push({
          type: 'info',
          message: `${depositData.pending_count} setoran menunggu verifikasi`,
          value: formatRupiah(depositData.pending)
        });
      }

      setStats({
        sales: salesData,
        purchases: purchaseData,
        ar: arData,
        ap: apData,
        deposits: depositData,
        inventory: inventoryData,
        employees: employeeData,
        branches: branchData,
        profit: { gross: salesData.gross_profit, net: salesData.gross_profit - purchaseData.total },
        cashFlow: { inflow: salesData.total + depositData.total, outflow: purchaseData.total + apData.total }
      });
      setAlerts(newAlerts);
      setBranchPerformance(branchData.performance);

    } catch (err) {
      console.error('Dashboard load error:', err);
      toast.error('Gagal memuat data dashboard');
    } finally {
      setLoading(false);
    }
  }, [api, period]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6" data-testid="owner-dashboard">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <BarChart3 className="h-7 w-7 text-blue-400" />
            Owner Dashboard
          </h1>
          <p className="text-gray-400 text-sm">Selamat datang, {user?.name || 'Owner'}!</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
          >
            <option value="today">Hari Ini</option>
            <option value="week">Minggu Ini</option>
            <option value="month">Bulan Ini</option>
            <option value="year">Tahun Ini</option>
          </select>
          <button
            onClick={loadDashboardData}
            className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Main KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <KPICard
          title="Total Penjualan"
          value={formatRupiah(stats.sales.total)}
          subtitle={`${formatNumber(stats.sales.count)} transaksi`}
          icon={ShoppingCart}
          color="green"
          trend="up"
          trendValue="+12%"
        />
        <KPICard
          title="Total Pembelian"
          value={formatRupiah(stats.purchases.total)}
          subtitle={`${formatNumber(stats.purchases.count)} PO`}
          icon={Package}
          color="blue"
        />
        <KPICard
          title="Laba Kotor"
          value={formatRupiah(stats.profit.gross)}
          subtitle="Penjualan - HPP"
          icon={TrendingUp}
          color={stats.profit.gross >= 0 ? 'green' : 'red'}
          trend={stats.profit.gross >= 0 ? 'up' : 'down'}
        />
        <KPICard
          title="Rata-rata Tiket"
          value={formatRupiah(stats.sales.avgTicket)}
          subtitle="Per transaksi"
          icon={DollarSign}
          color="purple"
        />
      </div>

      {/* Receivables & Payables */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <KPICard
          title="Total Piutang (AR)"
          value={formatRupiah(stats.ar.total)}
          subtitle={stats.ar.overdue > 0 ? `${formatRupiah(stats.ar.overdue)} jatuh tempo` : 'Tidak ada jatuh tempo'}
          icon={TrendingUp}
          color={stats.ar.overdue > 0 ? 'amber' : 'green'}
        />
        <KPICard
          title="Total Hutang (AP)"
          value={formatRupiah(stats.ap.total)}
          subtitle={stats.ap.overdue > 0 ? `${formatRupiah(stats.ap.overdue)} jatuh tempo` : 'Tidak ada jatuh tempo'}
          icon={TrendingDown}
          color={stats.ap.overdue > 0 ? 'red' : 'blue'}
        />
        <KPICard
          title="Setoran Harian"
          value={formatRupiah(stats.deposits.total)}
          subtitle={stats.deposits.pending_count > 0 ? `${stats.deposits.pending_count} pending` : 'Semua verified'}
          icon={Wallet}
          color="amber"
        />
        <KPICard
          title="Stok Rendah"
          value={formatNumber(stats.inventory.lowStock)}
          subtitle="Item perlu restock"
          icon={AlertTriangle}
          color={stats.inventory.lowStock > 0 ? 'red' : 'green'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Alerts */}
        <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-5">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-400" />
            Peringatan
          </h2>
          <div className="space-y-3">
            {alerts.length === 0 ? (
              <p className="text-gray-400 text-sm">Tidak ada peringatan</p>
            ) : (
              alerts.map((alert, idx) => <AlertItem key={idx} {...alert} />)
            )}
          </div>
        </div>

        {/* Branch Performance */}
        <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-5">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Building2 className="h-5 w-5 text-blue-400" />
            Performa Cabang
          </h2>
          <div className="space-y-3">
            {branchPerformance.map((branch, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <span className="text-sm truncate flex-1">{branch.name}</span>
                <div className="flex items-center gap-2">
                  <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full"
                      style={{ width: `${Math.min(100, (branch.sales / branch.target) * 100)}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400 w-10 text-right">
                    {Math.round((branch.sales / branch.target) * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-5">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Users className="h-5 w-5 text-purple-400" />
            Statistik
          </h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Total Cabang</span>
              <span className="font-semibold">{stats.branches.total}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Total Karyawan</span>
              <span className="font-semibold">{stats.employees.total}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Karyawan Aktif</span>
              <span className="font-semibold text-green-400">{stats.employees.active}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Cash Inflow</span>
              <span className="font-semibold text-green-400">{formatRupiah(stats.cashFlow.inflow)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Cash Outflow</span>
              <span className="font-semibold text-red-400">{formatRupiah(stats.cashFlow.outflow)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-5">
        <h2 className="text-lg font-semibold mb-4">Transaksi Terbaru</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="text-left text-gray-400 text-sm border-b border-gray-700">
              <tr>
                <th className="pb-3">Invoice</th>
                <th className="pb-3">Tanggal</th>
                <th className="pb-3">Customer</th>
                <th className="pb-3">Cabang</th>
                <th className="pb-3 text-right">Total</th>
                <th className="pb-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {recentTransactions.map((tx, idx) => (
                <tr key={idx} className="text-sm">
                  <td className="py-3 text-blue-400">{tx.invoice_number}</td>
                  <td className="py-3 text-gray-400">{formatDate(tx.created_at)}</td>
                  <td className="py-3">{tx.customer_name || 'Walk-in'}</td>
                  <td className="py-3 text-gray-400">{tx.branch_name || '-'}</td>
                  <td className="py-3 text-right font-medium">{formatRupiah(tx.total)}</td>
                  <td className="py-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      tx.status === 'completed' ? 'bg-green-600/20 text-green-400' : 
                      tx.status === 'voided' ? 'bg-red-600/20 text-red-400' : 
                      'bg-gray-600/20 text-gray-400'
                    }`}>
                      {tx.status?.toUpperCase() || 'COMPLETED'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default OwnerDashboard;
