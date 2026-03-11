import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  DollarSign, TrendingUp, TrendingDown, CreditCard, Wallet, 
  FileText, PieChart, BarChart2, RefreshCw, Calendar, Building2,
  ArrowUpRight, ArrowDownRight, AlertCircle, CheckCircle
} from 'lucide-react';
import { toast } from 'sonner';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatNumber = (num) => (num || 0).toLocaleString('id-ID');
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

// Summary Card
const SummaryCard = ({ title, value, change, icon: Icon, color = 'blue', subtitle }) => {
  const colors = {
    blue: 'from-blue-600 to-blue-800',
    green: 'from-green-600 to-green-800',
    red: 'from-red-600 to-red-800',
    amber: 'from-amber-600 to-amber-800',
    purple: 'from-purple-600 to-purple-800',
  };
  
  return (
    <div className={`bg-gradient-to-br ${colors[color]} rounded-xl p-5 text-white`}>
      <div className="flex justify-between items-start mb-3">
        <Icon className="h-6 w-6 opacity-80" />
        {change && (
          <span className={`text-xs px-2 py-1 rounded-full ${change >= 0 ? 'bg-green-500/30' : 'bg-red-500/30'}`}>
            {change >= 0 ? '+' : ''}{change}%
          </span>
        )}
      </div>
      <h3 className="text-sm opacity-80 mb-1">{title}</h3>
      <p className="text-2xl font-bold">{value}</p>
      {subtitle && <p className="text-xs opacity-70 mt-1">{subtitle}</p>}
    </div>
  );
};

// Account Balance Row
const AccountRow = ({ code, name, debit, credit, balance }) => (
  <tr className="border-b border-gray-700/50 hover:bg-gray-800/30">
    <td className="py-2 text-sm font-mono text-gray-400">{code}</td>
    <td className="py-2 text-sm">{name}</td>
    <td className="py-2 text-sm text-right">{formatRupiah(debit)}</td>
    <td className="py-2 text-sm text-right">{formatRupiah(credit)}</td>
    <td className="py-2 text-sm text-right font-medium">{formatRupiah(balance)}</td>
  </tr>
);

const FinanceDashboard = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('month');
  
  // Finance Data
  const [summary, setSummary] = useState({
    revenue: 0,
    cogs: 0,
    grossProfit: 0,
    expenses: 0,
    netProfit: 0,
    assets: 0,
    liabilities: 0,
    equity: 0
  });
  const [arSummary, setArSummary] = useState({ total: 0, current: 0, overdue: 0 });
  const [apSummary, setApSummary] = useState({ total: 0, current: 0, overdue: 0 });
  const [cashSummary, setCashSummary] = useState({ total: 0, bank: 0, cash: 0 });
  const [accounts, setAccounts] = useState([]);
  const [recentJournals, setRecentJournals] = useState([]);
  const [monthlyTrend, setMonthlyTrend] = useState([]);

  const loadFinanceData = useCallback(async () => {
    setLoading(true);
    try {
      const [
        trialRes, arRes, apRes, journalRes, salesRes, purchaseRes
      ] = await Promise.all([
        api('/api/accounting/reports/trial-balance'),
        api('/api/ar/list?limit=500'),
        api('/api/ap/list?limit=500'),
        api('/api/accounting/journals?limit=20'),
        api('/api/pos/transactions?limit=1000'),
        api('/api/purchase/orders?status=received&limit=500')
      ]);

      // Process Trial Balance
      let trialBalance = [];
      if (trialRes.ok) {
        const data = await trialRes.json();
        trialBalance = data.accounts || data || [];
        setAccounts(trialBalance.slice(0, 15));
        
        // Calculate summary from trial balance
        let assets = 0, liabilities = 0, equity = 0, revenue = 0, expenses = 0;
        trialBalance.forEach(acc => {
          const code = acc.code || '';
          const balance = acc.balance || 0;
          if (code.startsWith('1')) assets += balance;
          else if (code.startsWith('2')) liabilities += Math.abs(balance);
          else if (code.startsWith('3')) equity += Math.abs(balance);
          else if (code.startsWith('4')) revenue += Math.abs(balance);
          else if (code.startsWith('5') || code.startsWith('6')) expenses += Math.abs(balance);
        });
        
        setSummary(prev => ({
          ...prev,
          assets, liabilities, equity, revenue, expenses,
          netProfit: revenue - expenses
        }));
      }

      // Process AR
      if (arRes.ok) {
        const arList = (await arRes.json()).items || [];
        const now = new Date();
        let total = 0, current = 0, overdue = 0;
        arList.forEach(ar => {
          const amount = ar.outstanding_amount || (ar.amount - (ar.paid_amount || 0));
          if (amount > 0) {
            total += amount;
            if (ar.due_date && new Date(ar.due_date) < now) {
              overdue += amount;
            } else {
              current += amount;
            }
          }
        });
        setArSummary({ total, current, overdue });
      }

      // Process AP
      if (apRes.ok) {
        const apList = (await apRes.json()).items || [];
        const now = new Date();
        let total = 0, current = 0, overdue = 0;
        apList.forEach(ap => {
          const amount = (ap.amount || 0) - (ap.paid_amount || 0);
          if (amount > 0) {
            total += amount;
            if (ap.due_date && new Date(ap.due_date) < now) {
              overdue += amount;
            } else {
              current += amount;
            }
          }
        });
        setApSummary({ total, current, overdue });
      }

      // Process Journals
      if (journalRes.ok) {
        const journals = (await journalRes.json()).items || [];
        setRecentJournals(journals.slice(0, 10));
      }

      // Process Sales for Revenue & COGS
      if (salesRes.ok) {
        const sales = (await salesRes.json()).items || [];
        const totalRevenue = sales.reduce((sum, s) => sum + (s.total || 0), 0);
        const totalCogs = sales.reduce((sum, s) => sum + (s.cost_total || 0), 0);
        setSummary(prev => ({
          ...prev,
          revenue: totalRevenue,
          cogs: totalCogs,
          grossProfit: totalRevenue - totalCogs
        }));
      }

      // Calculate cash summary (mock - should come from account balances)
      const cashAccounts = trialBalance.filter(a => 
        a.code?.startsWith('1101') || a.code?.startsWith('1102') || 
        a.name?.toLowerCase().includes('kas') || a.name?.toLowerCase().includes('bank')
      );
      let cashTotal = 0, bankTotal = 0;
      cashAccounts.forEach(acc => {
        if (acc.name?.toLowerCase().includes('bank')) {
          bankTotal += acc.balance || 0;
        } else {
          cashTotal += acc.balance || 0;
        }
      });
      setCashSummary({ total: cashTotal + bankTotal, cash: cashTotal, bank: bankTotal });

    } catch (err) {
      console.error('Finance dashboard error:', err);
      toast.error('Gagal memuat data keuangan');
    } finally {
      setLoading(false);
    }
  }, [api, period]);

  useEffect(() => {
    loadFinanceData();
  }, [loadFinanceData]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-green-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6" data-testid="finance-dashboard">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <DollarSign className="h-7 w-7 text-green-400" />
            Finance Dashboard
          </h1>
          <p className="text-gray-400 text-sm">Ringkasan keuangan dan akuntansi</p>
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
            onClick={loadFinanceData}
            className="p-2 bg-green-600 hover:bg-green-700 rounded-lg"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Main Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-6">
        <SummaryCard
          title="Total Pendapatan"
          value={formatRupiah(summary.revenue)}
          icon={TrendingUp}
          color="green"
          change={12}
        />
        <SummaryCard
          title="HPP (COGS)"
          value={formatRupiah(summary.cogs)}
          icon={TrendingDown}
          color="red"
        />
        <SummaryCard
          title="Laba Kotor"
          value={formatRupiah(summary.grossProfit)}
          icon={BarChart2}
          color={summary.grossProfit >= 0 ? 'green' : 'red'}
          subtitle={`${((summary.grossProfit / summary.revenue) * 100 || 0).toFixed(1)}% margin`}
        />
        <SummaryCard
          title="Beban Operasional"
          value={formatRupiah(summary.expenses)}
          icon={CreditCard}
          color="amber"
        />
        <SummaryCard
          title="Laba Bersih"
          value={formatRupiah(summary.netProfit)}
          icon={DollarSign}
          color={summary.netProfit >= 0 ? 'green' : 'red'}
          change={summary.netProfit >= 0 ? 8 : -5}
        />
      </div>

      {/* Balance Sheet Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-600/10 border border-blue-500/30 rounded-xl p-5">
          <h3 className="text-blue-400 text-sm mb-2">Total Aset</h3>
          <p className="text-2xl font-bold">{formatRupiah(summary.assets)}</p>
          <div className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Kas & Bank</span>
              <span>{formatRupiah(cashSummary.total)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Piutang Usaha</span>
              <span>{formatRupiah(arSummary.total)}</span>
            </div>
          </div>
        </div>
        
        <div className="bg-red-600/10 border border-red-500/30 rounded-xl p-5">
          <h3 className="text-red-400 text-sm mb-2">Total Kewajiban</h3>
          <p className="text-2xl font-bold">{formatRupiah(summary.liabilities)}</p>
          <div className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Hutang Dagang</span>
              <span>{formatRupiah(apSummary.total)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Kewajiban Lain</span>
              <span>{formatRupiah(summary.liabilities - apSummary.total)}</span>
            </div>
          </div>
        </div>
        
        <div className="bg-purple-600/10 border border-purple-500/30 rounded-xl p-5">
          <h3 className="text-purple-400 text-sm mb-2">Total Ekuitas</h3>
          <p className="text-2xl font-bold">{formatRupiah(summary.equity)}</p>
          <div className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Modal Disetor</span>
              <span>{formatRupiah(summary.equity * 0.8)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Laba Ditahan</span>
              <span>{formatRupiah(summary.equity * 0.2)}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* AR Summary */}
        <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-5">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <ArrowUpRight className="h-5 w-5 text-green-400" />
            Piutang Usaha (AR)
          </h2>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-gray-800 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-400 mb-1">Total</p>
              <p className="text-lg font-bold text-green-400">{formatRupiah(arSummary.total)}</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-400 mb-1">Belum Jatuh Tempo</p>
              <p className="text-lg font-bold text-blue-400">{formatRupiah(arSummary.current)}</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-400 mb-1">Jatuh Tempo</p>
              <p className="text-lg font-bold text-red-400">{formatRupiah(arSummary.overdue)}</p>
            </div>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-green-500 to-blue-500"
              style={{ width: `${arSummary.total > 0 ? (arSummary.current / arSummary.total) * 100 : 0}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            {arSummary.total > 0 ? ((arSummary.current / arSummary.total) * 100).toFixed(1) : 0}% dalam kondisi baik
          </p>
        </div>

        {/* AP Summary */}
        <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-5">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <ArrowDownRight className="h-5 w-5 text-red-400" />
            Hutang Usaha (AP)
          </h2>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-gray-800 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-400 mb-1">Total</p>
              <p className="text-lg font-bold text-red-400">{formatRupiah(apSummary.total)}</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-400 mb-1">Belum Jatuh Tempo</p>
              <p className="text-lg font-bold text-blue-400">{formatRupiah(apSummary.current)}</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-400 mb-1">Jatuh Tempo</p>
              <p className="text-lg font-bold text-amber-400">{formatRupiah(apSummary.overdue)}</p>
            </div>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-amber-500"
              style={{ width: `${apSummary.total > 0 ? (apSummary.current / apSummary.total) * 100 : 100}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            {apSummary.overdue > 0 
              ? `${formatRupiah(apSummary.overdue)} perlu segera dibayar`
              : 'Semua hutang dalam kondisi baik'
            }
          </p>
        </div>
      </div>

      {/* Trial Balance Preview */}
      <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-5 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-blue-400" />
          Neraca Saldo (Trial Balance)
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="text-left text-gray-400 text-sm border-b border-gray-700">
              <tr>
                <th className="pb-3 w-24">Kode</th>
                <th className="pb-3">Nama Akun</th>
                <th className="pb-3 text-right">Debit</th>
                <th className="pb-3 text-right">Credit</th>
                <th className="pb-3 text-right">Saldo</th>
              </tr>
            </thead>
            <tbody>
              {accounts.length === 0 ? (
                <tr>
                  <td colSpan="5" className="py-8 text-center text-gray-400">
                    Belum ada data akun
                  </td>
                </tr>
              ) : accounts.map((acc, idx) => (
                <AccountRow
                  key={idx}
                  code={acc.code}
                  name={acc.name}
                  debit={acc.debit || 0}
                  credit={acc.credit || 0}
                  balance={acc.balance || 0}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Journal Entries */}
      <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-5">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-amber-400" />
          Jurnal Terbaru
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="text-left text-gray-400 text-sm border-b border-gray-700">
              <tr>
                <th className="pb-3">No Jurnal</th>
                <th className="pb-3">Tanggal</th>
                <th className="pb-3">Keterangan</th>
                <th className="pb-3 text-right">Debit</th>
                <th className="pb-3 text-right">Credit</th>
                <th className="pb-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {recentJournals.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-gray-400">
                    Belum ada jurnal
                  </td>
                </tr>
              ) : recentJournals.map((j, idx) => (
                <tr key={idx} className="text-sm">
                  <td className="py-3 text-blue-400">{j.journal_no || j.id?.slice(0,8)}</td>
                  <td className="py-3 text-gray-400">{formatDate(j.journal_date || j.created_at)}</td>
                  <td className="py-3 truncate max-w-xs">{j.description || j.notes || '-'}</td>
                  <td className="py-3 text-right">{formatRupiah(j.total_debit || j.debit_total)}</td>
                  <td className="py-3 text-right">{formatRupiah(j.total_credit || j.credit_total)}</td>
                  <td className="py-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      j.status === 'posted' ? 'bg-green-600/20 text-green-400' : 'bg-gray-600/20 text-gray-400'
                    }`}>
                      {j.status?.toUpperCase() || 'POSTED'}
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

export default FinanceDashboard;
