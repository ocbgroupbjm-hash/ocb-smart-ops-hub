import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Wallet, Search, Loader2, Plus, ArrowDownLeft, ArrowUpRight, ArrowLeftRight,
  RefreshCw, Calendar, Building2, Filter, Download
} from 'lucide-react';
import { toast } from 'sonner';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (dateStr) => dateStr ? new Date(dateStr).toLocaleDateString('id-ID') : '-';

// Transaction type badge
const TypeBadge = ({ type, direction }) => {
  const configs = {
    cash_in: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: ArrowDownLeft },
    cash_out: { bg: 'bg-rose-500/20', text: 'text-rose-400', icon: ArrowUpRight },
    ap_payment: { bg: 'bg-orange-500/20', text: 'text-orange-400', icon: ArrowUpRight },
    ar_receipt: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: ArrowDownLeft },
    bank_transfer: { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: ArrowLeftRight },
    expense: { bg: 'bg-pink-500/20', text: 'text-pink-400', icon: ArrowUpRight },
    revenue: { bg: 'bg-teal-500/20', text: 'text-teal-400', icon: ArrowDownLeft },
  };
  
  const config = configs[type] || { bg: 'bg-gray-500/20', text: 'text-gray-400', icon: ArrowLeftRight };
  const Icon = config.icon;
  
  const typeNames = {
    cash_in: 'Kas Masuk',
    cash_out: 'Kas Keluar',
    ap_payment: 'Bayar Hutang',
    ar_receipt: 'Terima Piutang',
    bank_transfer: 'Transfer',
    expense: 'Biaya',
    revenue: 'Pendapatan'
  };
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 ${config.bg} ${config.text} rounded text-xs font-medium`}>
      <Icon className="h-3 w-3" />
      {typeNames[type] || type}
    </span>
  );
};

const CashBankLedgerPage = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [entries, setEntries] = useState([]);
  const [loadingEntries, setLoadingEntries] = useState(false);
  const [summary, setSummary] = useState(null);
  
  // Filters
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(1);
    return d.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [transactionType, setTransactionType] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    loadAccounts();
    loadSummary();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      loadEntries();
    }
  }, [selectedAccount, startDate, endDate, transactionType, page]);

  const loadAccounts = async () => {
    try {
      const res = await api('/api/cashflow/accounts');
      if (res.ok) {
        const data = await res.json();
        setAccounts(data.accounts || []);
        // Auto-select first account
        if (data.accounts?.length > 0 && !selectedAccount) {
          setSelectedAccount(data.accounts[0].account_code);
        }
      }
    } catch (err) {
      console.error('Load accounts error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadEntries = async () => {
    setLoadingEntries(true);
    try {
      let url = `/api/cashflow/ledger?page=${page}&limit=50`;
      if (selectedAccount) url += `&account_code=${selectedAccount}`;
      if (startDate) url += `&start_date=${startDate}`;
      if (endDate) url += `&end_date=${endDate}`;
      if (transactionType) url += `&transaction_type=${transactionType}`;
      
      const res = await api(url);
      if (res.ok) {
        const data = await res.json();
        setEntries(data.items || []);
        setTotalPages(data.pages || 1);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoadingEntries(false);
    }
  };

  const loadSummary = async () => {
    try {
      const res = await api(`/api/cashflow/summary?start_date=${startDate}&end_date=${endDate}`);
      if (res.ok) {
        const data = await res.json();
        setSummary(data);
      }
    } catch (err) {
      console.error('Load summary error:', err);
    }
  };

  const selectedAccountInfo = accounts.find(a => a.account_code === selectedAccount);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100" data-testid="page-title">Mutasi Kas/Bank</h1>
          <p className="text-gray-400">Ledger dan histori transaksi kas/bank</p>
        </div>
        <button
          onClick={() => { loadAccounts(); loadEntries(); loadSummary(); }}
          className="flex items-center gap-2 px-4 py-2 bg-[#1a1214] border border-red-900/30 text-gray-300 rounded-lg hover:bg-red-900/20"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Account Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {accounts.map(acc => (
          <button
            key={acc.account_code}
            onClick={() => { setSelectedAccount(acc.account_code); setPage(1); }}
            data-testid={`account-card-${acc.account_code}`}
            className={`p-4 rounded-xl border transition-all text-left ${
              selectedAccount === acc.account_code
                ? 'bg-amber-600/20 border-amber-500'
                : 'bg-[#1a1214] border-red-900/30 hover:border-amber-600/50'
            }`}
          >
            <div className="flex items-center gap-3 mb-2">
              <div className={`p-2 rounded-lg ${
                acc.account_type === 'bank' ? 'bg-blue-600/20' : 'bg-emerald-600/20'
              }`}>
                <Wallet className={`h-5 w-5 ${
                  acc.account_type === 'bank' ? 'text-blue-400' : 'text-emerald-400'
                }`} />
              </div>
              <div>
                <div className="text-xs text-gray-500 font-mono">{acc.account_code}</div>
                <div className="text-sm text-amber-100 font-medium">{acc.account_name}</div>
              </div>
            </div>
            <div className="text-xl font-bold text-amber-400 font-mono">
              {formatRupiah(acc.balance)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {acc.transaction_count} transaksi
            </div>
          </button>
        ))}
        
        {/* Total Balance Card */}
        <div className="p-4 rounded-xl bg-gradient-to-br from-amber-900/30 to-red-900/30 border border-amber-600/30">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-amber-600/20 rounded-lg">
              <Wallet className="h-5 w-5 text-amber-400" />
            </div>
            <div>
              <div className="text-xs text-amber-200/70">TOTAL SALDO</div>
              <div className="text-sm text-amber-100 font-medium">Semua Akun</div>
            </div>
          </div>
          <div className="text-2xl font-bold text-amber-300 font-mono">
            {formatRupiah(accounts.reduce((sum, a) => sum + (a.balance || 0), 0))}
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-emerald-900/20 border border-emerald-600/30 rounded-xl p-4">
            <div className="flex items-center gap-2 text-emerald-400 mb-2">
              <ArrowDownLeft className="h-5 w-5" />
              <span className="text-sm">Total Kas Masuk</span>
            </div>
            <div className="text-2xl font-bold text-emerald-300 font-mono">
              {formatRupiah(summary.total_cash_in)}
            </div>
          </div>
          <div className="bg-rose-900/20 border border-rose-600/30 rounded-xl p-4">
            <div className="flex items-center gap-2 text-rose-400 mb-2">
              <ArrowUpRight className="h-5 w-5" />
              <span className="text-sm">Total Kas Keluar</span>
            </div>
            <div className="text-2xl font-bold text-rose-300 font-mono">
              {formatRupiah(summary.total_cash_out)}
            </div>
          </div>
          <div className="bg-amber-900/20 border border-amber-600/30 rounded-xl p-4">
            <div className="flex items-center gap-2 text-amber-400 mb-2">
              <ArrowLeftRight className="h-5 w-5" />
              <span className="text-sm">Net Cashflow</span>
            </div>
            <div className={`text-2xl font-bold font-mono ${
              summary.net_cashflow >= 0 ? 'text-emerald-300' : 'text-rose-300'
            }`}>
              {formatRupiah(summary.net_cashflow)}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <input
              type="date"
              value={startDate}
              onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
              className="px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100 text-sm"
            />
            <span className="text-gray-500">-</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
              className="px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100 text-sm"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={transactionType}
              onChange={(e) => { setTransactionType(e.target.value); setPage(1); }}
              className="px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100 text-sm"
            >
              <option value="">Semua Tipe</option>
              <option value="cash_in">Kas Masuk</option>
              <option value="cash_out">Kas Keluar</option>
              <option value="ap_payment">Bayar Hutang</option>
              <option value="ar_receipt">Terima Piutang</option>
              <option value="bank_transfer">Transfer</option>
            </select>
          </div>
          
          <button
            onClick={() => { loadEntries(); loadSummary(); }}
            className="px-4 py-2 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 text-sm"
          >
            Filter
          </button>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-amber-100">
            {selectedAccountInfo ? `${selectedAccountInfo.account_code} - ${selectedAccountInfo.account_name}` : 'Mutasi Kas/Bank'}
          </h3>
          <span className="text-sm text-gray-400">
            {entries.length} transaksi
          </span>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Tanggal</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">No. Transaksi</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Tipe</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Keterangan</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Counterparty</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-amber-200 uppercase">Debit</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-amber-200 uppercase">Kredit</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Journal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loadingEntries ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center">
                    <Loader2 className="h-6 w-6 animate-spin text-amber-500 mx-auto" />
                  </td>
                </tr>
              ) : entries.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                    Tidak ada transaksi
                  </td>
                </tr>
              ) : (
                entries.map(entry => (
                  <tr key={entry.id} className="hover:bg-red-900/10">
                    <td className="px-4 py-3 text-gray-300">{formatDate(entry.transaction_date)}</td>
                    <td className="px-4 py-3 font-mono text-sm text-amber-100">{entry.transaction_no}</td>
                    <td className="px-4 py-3">
                      <TypeBadge type={entry.transaction_type} direction={entry.direction} />
                    </td>
                    <td className="px-4 py-3 text-gray-300 text-sm max-w-xs truncate">{entry.description}</td>
                    <td className="px-4 py-3 text-gray-400 text-sm">{entry.counterparty_name || '-'}</td>
                    <td className="px-4 py-3 text-right font-mono text-emerald-400">
                      {entry.debit > 0 ? formatRupiah(entry.debit) : '-'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-rose-400">
                      {entry.credit > 0 ? formatRupiah(entry.credit) : '-'}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{entry.journal_no}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-red-900/30 flex items-center justify-between">
            <span className="text-sm text-gray-400">
              Halaman {page} dari {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-3 py-1 bg-[#0a0608] border border-red-900/30 rounded text-gray-300 disabled:opacity-50"
              >
                Prev
              </button>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 bg-[#0a0608] border border-red-900/30 rounded text-gray-300 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CashBankLedgerPage;
