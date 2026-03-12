import React, { useState, useEffect, useCallback } from 'react';
import { 
  FileText, TrendingUp, Package, DollarSign, CreditCard, Wallet, 
  RefreshCw, Download, Calendar, Filter, ChevronRight, BarChart3,
  ShoppingCart, Users, Building2, Truck, AlertTriangle, Clock,
  ArrowUp, ArrowDown, Minus
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Format helpers
const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatPercent = (num) => `${(num || 0).toFixed(1)}%`;

// Report Category Card
const CategoryCard = ({ category, icon: Icon, reports, onSelect, activeReport }) => (
  <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
    <div className="p-3 bg-red-900/20 flex items-center gap-2">
      <Icon className="h-4 w-4 text-amber-400" />
      <span className="text-amber-100 font-medium text-sm">{category}</span>
    </div>
    <div className="p-2 space-y-1">
      {reports.map((report, idx) => (
        <button
          key={idx}
          onClick={() => onSelect(report.endpoint)}
          className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center justify-between ${
            activeReport === report.endpoint 
              ? 'bg-amber-600/20 text-amber-100' 
              : 'text-gray-400 hover:bg-red-900/20 hover:text-gray-200'
          }`}
          data-testid={`report-${report.name.replace(/\s+/g, '-').toLowerCase()}`}
        >
          {report.name}
          <ChevronRight className="h-4 w-4 opacity-50" />
        </button>
      ))}
    </div>
  </div>
);

// Summary Card
const SummaryCard = ({ label, value, subValue, icon: Icon, trend, color = "amber" }) => {
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
  
  return (
    <div className={`bg-gradient-to-br ${colors[color]} border rounded-xl p-4`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-400 mb-1">{label}</p>
          <p className="text-lg font-bold text-amber-100">{value}</p>
          {subValue && <p className="text-xs text-gray-500 mt-1">{subValue}</p>}
        </div>
        <div className={`h-10 w-10 rounded-lg ${iconColors[color]} flex items-center justify-center`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      {trend !== undefined && (
        <div className={`mt-2 flex items-center gap-1 text-xs ${trend > 0 ? 'text-green-400' : trend < 0 ? 'text-red-400' : 'text-gray-400'}`}>
          {trend > 0 ? <ArrowUp className="h-3 w-3" /> : trend < 0 ? <ArrowDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
          {Math.abs(trend).toFixed(1)}%
        </div>
      )}
    </div>
  );
};

// Aging Badge
const AgingBadge = ({ bucket, amount, count }) => {
  const colors = {
    current: 'bg-green-500/20 text-green-300 border-green-500/30',
    '1_30': 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    '31_60': 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    '61_90': 'bg-red-500/20 text-red-300 border-red-500/30',
    'over_90': 'bg-red-700/20 text-red-200 border-red-700/30'
  };
  
  const labels = {
    current: 'Current',
    '1_30': '1-30 days',
    '31_60': '31-60 days',
    '61_90': '61-90 days',
    'over_90': '> 90 days'
  };
  
  return (
    <div className={`p-3 rounded-lg border ${colors[bucket]}`}>
      <p className="text-xs opacity-70">{labels[bucket]}</p>
      <p className="text-lg font-bold">{formatRupiah(amount)}</p>
      <p className="text-xs opacity-50">{count} item(s)</p>
    </div>
  );
};

const ReportCenter = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [reportCategories, setReportCategories] = useState([]);
  const [activeReport, setActiveReport] = useState('');
  const [reportData, setReportData] = useState(null);
  
  // Filters
  const [period, setPeriod] = useState('month');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Load report categories
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await fetch(`${API_URL}/api/reports/`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        setReportCategories(data.reports || []);
      } catch (err) {
        console.error(err);
      }
    };
    if (token) fetchCategories();
  }, [token]);

  // Fetch report data
  const fetchReport = useCallback(async (endpoint) => {
    if (!endpoint) return;
    
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      params.append('period', period);
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      
      const res = await fetch(`${API_URL}${endpoint}?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await res.json();
      setReportData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [token, period, dateFrom, dateTo]);

  const handleSelectReport = (endpoint) => {
    setActiveReport(endpoint);
    fetchReport(endpoint);
  };

  // Export report
  const handleExport = () => {
    if (!reportData) return;
    
    const dataStr = JSON.stringify(reportData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report_${reportData.report_type || 'data'}_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
  };

  // Get category icon
  const getCategoryIcon = (category) => {
    const icons = {
      'Sales': ShoppingCart,
      'Purchase': Truck,
      'Inventory': Package,
      'Financial': DollarSign,
      'Receivables': CreditCard,
      'Payables': Building2,
      'Cash Flow': Wallet
    };
    return icons[category] || FileText;
  };

  // Render report content based on type
  const renderReportContent = () => {
    if (!reportData) return null;
    
    const type = reportData.report_type;
    
    // Sales Summary
    if (type === 'sales_summary') {
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-4 gap-4">
            <SummaryCard label="Total Penjualan" value={formatRupiah(reportData.summary?.total_sales)} icon={DollarSign} color="green" />
            <SummaryCard label="Total Transaksi" value={reportData.summary?.total_transactions} icon={ShoppingCart} color="blue" />
            <SummaryCard label="Rata-rata" value={formatRupiah(reportData.summary?.average_transaction)} icon={TrendingUp} color="amber" />
            <SummaryCard label="Total Qty" value={reportData.summary?.total_qty?.toLocaleString()} icon={Package} color="purple" />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
              <h4 className="text-amber-100 font-medium mb-3">By Payment Method</h4>
              <div className="space-y-2">
                {Object.entries(reportData.by_payment_method || {}).map(([method, data]) => (
                  <div key={method} className="flex justify-between items-center p-2 bg-black/20 rounded">
                    <span className="text-gray-300 capitalize">{method}</span>
                    <div className="text-right">
                      <span className="text-amber-100 font-medium">{formatRupiah(data.total)}</span>
                      <span className="text-gray-500 text-xs ml-2">({data.count} txn)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
              <h4 className="text-amber-100 font-medium mb-3">Daily Trend</h4>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {reportData.daily_breakdown?.slice(-10).map((day) => (
                  <div key={day.date} className="flex justify-between items-center p-2 bg-black/20 rounded text-sm">
                    <span className="text-gray-400">{day.date}</span>
                    <span className="text-green-400">{formatRupiah(day.total)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    // Sales by Product/Customer
    if (type === 'sales_by_product' || type === 'sales_by_customer' || type === 'sales_by_salesperson') {
      return (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs text-amber-200">No</th>
                <th className="px-4 py-3 text-left text-xs text-amber-200">
                  {type === 'sales_by_product' ? 'Produk' : type === 'sales_by_customer' ? 'Customer' : 'Salesperson'}
                </th>
                <th className="px-4 py-3 text-right text-xs text-amber-200">Qty</th>
                <th className="px-4 py-3 text-right text-xs text-amber-200">Total</th>
                <th className="px-4 py-3 text-right text-xs text-amber-200">Transaksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {reportData.items?.map((item, idx) => (
                <tr key={idx} className="hover:bg-red-900/10">
                  <td className="px-4 py-3 text-gray-400">{idx + 1}</td>
                  <td className="px-4 py-3">
                    <div className="text-amber-100">{item.product_name || item.customer_name || item.salesperson_name}</div>
                    {item.product_code && <div className="text-xs text-gray-500">{item.product_code}</div>}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-300">{item.total_qty?.toLocaleString() || '-'}</td>
                  <td className="px-4 py-3 text-right text-green-400">{formatRupiah(item.total_sales || item.total_purchases)}</td>
                  <td className="px-4 py-3 text-right text-gray-400">{item.transaction_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }
    
    // Inventory Stock Status
    if (type === 'inventory_stock_status') {
      return (
        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            <SummaryCard label="Total Produk" value={reportData.summary?.total_products} icon={Package} color="blue" />
            <SummaryCard label="Stok Rendah" value={reportData.summary?.low_stock_count} icon={AlertTriangle} color="amber" />
            <SummaryCard label="Habis" value={reportData.summary?.out_of_stock_count} icon={AlertTriangle} color="red" />
            <SummaryCard label="Nilai Stok" value={formatRupiah(reportData.summary?.total_stock_value)} icon={DollarSign} color="green" />
          </div>
          
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-red-900/20">
                <tr>
                  <th className="px-4 py-3 text-left text-xs text-amber-200">Produk</th>
                  <th className="px-4 py-3 text-right text-xs text-amber-200">Stok</th>
                  <th className="px-4 py-3 text-right text-xs text-amber-200">Min</th>
                  <th className="px-4 py-3 text-right text-xs text-amber-200">Nilai</th>
                  <th className="px-4 py-3 text-center text-xs text-amber-200">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/20">
                {reportData.items?.slice(0, 50).map((item, idx) => (
                  <tr key={idx} className="hover:bg-red-900/10">
                    <td className="px-4 py-3">
                      <div className="text-amber-100">{item.product_name}</div>
                      <div className="text-xs text-gray-500">{item.product_code}</div>
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300">{item.current_stock} {item.unit}</td>
                    <td className="px-4 py-3 text-right text-gray-500">{item.min_stock}</td>
                    <td className="px-4 py-3 text-right text-green-400">{formatRupiah(item.stock_value)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 text-xs rounded ${
                        item.status === 'out_of_stock' ? 'bg-red-500/20 text-red-300' :
                        item.status === 'low_stock' ? 'bg-amber-500/20 text-amber-300' :
                        'bg-green-500/20 text-green-300'
                      }`}>
                        {item.status === 'out_of_stock' ? 'Habis' : item.status === 'low_stock' ? 'Rendah' : 'Normal'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }
    
    // Profit & Loss
    if (type === 'profit_loss') {
      return (
        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            <SummaryCard label="Total Revenue" value={formatRupiah(reportData.revenue?.total_revenue)} icon={TrendingUp} color="green" />
            <SummaryCard label="COGS" value={formatRupiah(reportData.cost_of_goods_sold)} icon={Package} color="blue" />
            <SummaryCard label="Gross Profit" value={formatRupiah(reportData.gross_profit)} subValue={formatPercent(reportData.gross_margin_percent)} icon={DollarSign} color="amber" />
            <SummaryCard label="Net Profit" value={formatRupiah(reportData.net_profit)} subValue={formatPercent(reportData.net_margin_percent)} icon={Wallet} color={reportData.net_profit >= 0 ? "green" : "red"} />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
              <h4 className="text-amber-100 font-medium mb-3">Revenue</h4>
              <div className="space-y-2">
                <div className="flex justify-between p-2 bg-black/20 rounded">
                  <span className="text-gray-400">Sales Revenue</span>
                  <span className="text-green-400">{formatRupiah(reportData.revenue?.sales_revenue)}</span>
                </div>
              </div>
            </div>
            
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
              <h4 className="text-amber-100 font-medium mb-3">Operating Expenses</h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {Object.entries(reportData.operating_expenses?.breakdown || {}).map(([name, amount]) => (
                  <div key={name} className="flex justify-between p-2 bg-black/20 rounded text-sm">
                    <span className="text-gray-400">{name}</span>
                    <span className="text-red-400">{formatRupiah(amount)}</span>
                  </div>
                ))}
                {Object.keys(reportData.operating_expenses?.breakdown || {}).length === 0 && (
                  <p className="text-gray-500 text-sm">No expenses recorded</p>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    // AR/AP Aging
    if (type === 'ar_aging' || type === 'ap_aging') {
      const isAR = type === 'ar_aging';
      return (
        <div className="space-y-4">
          <SummaryCard 
            label={isAR ? "Total Piutang" : "Total Hutang"} 
            value={formatRupiah(isAR ? reportData.total_ar : reportData.total_ap)} 
            icon={isAR ? CreditCard : Building2} 
            color={isAR ? "blue" : "red"} 
          />
          
          <div className="grid grid-cols-5 gap-4">
            {Object.entries(reportData.aging_buckets || {}).map(([bucket, data]) => (
              <AgingBadge key={bucket} bucket={bucket} amount={data.amount} count={data.count} />
            ))}
          </div>
          
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
            <h4 className="text-amber-100 font-medium mb-3">Detail {'>'}90 Days</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {reportData.aging_buckets?.over_90?.items?.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center p-2 bg-black/20 rounded text-sm">
                  <div>
                    <span className="text-amber-100">{isAR ? item.invoice_no : item.po_no}</span>
                    <span className="text-gray-500 ml-2">{isAR ? item.customer : item.supplier}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-red-400">{formatRupiah(item.amount)}</span>
                    <span className="text-gray-500 text-xs ml-2">{item.days_overdue} days</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }
    
    // Cash Flow
    if (type === 'cashflow_summary') {
      return (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <SummaryCard label="Total Inflows" value={formatRupiah(reportData.inflows?.total)} icon={ArrowUp} color="green" />
            <SummaryCard label="Total Outflows" value={formatRupiah(reportData.outflows?.total)} icon={ArrowDown} color="red" />
            <SummaryCard label="Net Cash Flow" value={formatRupiah(reportData.net_cash_flow)} icon={Wallet} color={reportData.net_cash_flow >= 0 ? "green" : "red"} />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#1a1214] border border-green-900/30 rounded-xl p-4">
              <h4 className="text-green-300 font-medium mb-3 flex items-center gap-2">
                <ArrowUp className="h-4 w-4" /> Cash Inflows
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between p-2 bg-black/20 rounded">
                  <span className="text-gray-400">Cash Sales</span>
                  <span className="text-green-400">{formatRupiah(reportData.inflows?.cash_sales)}</span>
                </div>
                <div className="flex justify-between p-2 bg-black/20 rounded">
                  <span className="text-gray-400">POS Cash</span>
                  <span className="text-green-400">{formatRupiah(reportData.inflows?.pos_cash)}</span>
                </div>
                <div className="flex justify-between p-2 bg-black/20 rounded">
                  <span className="text-gray-400">AR Collections</span>
                  <span className="text-green-400">{formatRupiah(reportData.inflows?.ar_collections)}</span>
                </div>
              </div>
            </div>
            
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
              <h4 className="text-red-300 font-medium mb-3 flex items-center gap-2">
                <ArrowDown className="h-4 w-4" /> Cash Outflows
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between p-2 bg-black/20 rounded">
                  <span className="text-gray-400">Supplier Payments</span>
                  <span className="text-red-400">{formatRupiah(reportData.outflows?.supplier_payments)}</span>
                </div>
                <div className="flex justify-between p-2 bg-black/20 rounded">
                  <span className="text-gray-400">Operating Expenses</span>
                  <span className="text-red-400">{formatRupiah(reportData.outflows?.operating_expenses)}</span>
                </div>
                <div className="flex justify-between p-2 bg-black/20 rounded">
                  <span className="text-gray-400">Commission</span>
                  <span className="text-red-400">{formatRupiah(reportData.outflows?.commission_payments)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    // Default: Show raw JSON
    return (
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <pre className="text-xs text-gray-400 overflow-auto max-h-96">
          {JSON.stringify(reportData, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <div className="space-y-6" data-testid="report-center-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Report Center</h1>
          <p className="text-gray-400 text-sm mt-1">Business Intelligence & Analytics</p>
        </div>
        <div className="flex gap-2">
          {reportData && (
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
              data-testid="export-btn"
            >
              <Download className="h-4 w-4" />
              Export
            </button>
          )}
          <button
            onClick={() => fetchReport(activeReport)}
            disabled={!activeReport}
            className="flex items-center gap-2 px-4 py-2 bg-red-900/30 hover:bg-red-900/50 text-amber-100 rounded-lg disabled:opacity-50"
            data-testid="refresh-btn"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 items-center bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-gray-400" />
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-3 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100 text-sm"
            data-testid="period-select"
          >
            <option value="today">Hari Ini</option>
            <option value="week">Minggu Ini</option>
            <option value="month">Bulan Ini</option>
            <option value="quarter">Kuartal Ini</option>
            <option value="year">Tahun Ini</option>
          </select>
        </div>
        
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="px-3 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100 text-sm"
            placeholder="From"
          />
          <span className="text-gray-500">-</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="px-3 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100 text-sm"
            placeholder="To"
          />
        </div>
        
        {activeReport && (
          <button
            onClick={() => fetchReport(activeReport)}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm"
          >
            Apply Filter
          </button>
        )}
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Sidebar - Report Categories */}
        <div className="col-span-3 space-y-4">
          {reportCategories.map((cat, idx) => (
            <CategoryCard
              key={idx}
              category={cat.category}
              icon={getCategoryIcon(cat.category)}
              reports={cat.reports}
              onSelect={handleSelectReport}
              activeReport={activeReport}
            />
          ))}
        </div>

        {/* Main Content - Report Data */}
        <div className="col-span-9">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <RefreshCw className="h-8 w-8 text-amber-500 animate-spin" />
            </div>
          ) : !activeReport ? (
            <div className="text-center py-20 text-gray-500">
              <BarChart3 className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <p className="text-lg">Pilih laporan dari sidebar</p>
              <p className="text-sm mt-1">untuk melihat data dan analisis</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Report Header */}
              {reportData?.period && (
                <div className="flex items-center gap-4 text-sm text-gray-400">
                  <span>Period: {reportData.period.start} - {reportData.period.end}</span>
                  <span>Type: {reportData.report_type}</span>
                </div>
              )}
              
              {/* Report Content */}
              {renderReportContent()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportCenter;
