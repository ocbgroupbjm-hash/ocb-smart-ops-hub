import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Search, Download, Printer, Loader2, FileText, ChevronDown, ChevronRight, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { getDefaultFilterDates, formatDateDisplay } from '../../utils/dateUtils';

const GeneralLedger = () => {
  const { api } = useAuth();
  const [ledgerData, setLedgerData] = useState([]);  // Array of account summaries
  const [accountDetails, setAccountDetails] = useState({});  // Details per account
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState({});
  const { dateFrom: defaultFrom, dateTo: defaultTo } = getDefaultFilterDates();
  const [dateFrom, setDateFrom] = useState(defaultFrom);
  const [dateTo, setDateTo] = useState(defaultTo);
  const [expandedAccounts, setExpandedAccounts] = useState({});

  // Load all account summaries from Trial Balance
  const loadLedger = useCallback(async () => {
    setLoading(true);
    try {
      // Use trial-balance to get all accounts with balances
      const params = new URLSearchParams({
        ...(dateTo && { date: dateTo })
      });
      const res = await api(`/api/accounting/financial/trial-balance?${params}`);
      if (res.ok) {
        const data = await res.json();
        const accounts = data.accounts || [];
        // Transform to ledger format
        setLedgerData(accounts.map(acc => ({
          account_id: acc.account_code,
          account_code: acc.account_code,
          account_name: acc.account_name,
          total_debit: acc.debit || 0,
          total_credit: acc.credit || 0,
          balance: (acc.debit || 0) - (acc.credit || 0),
          entries: []  // Will load on expand
        })));
      }
    } catch (err) { 
      toast.error('Gagal memuat data'); 
      console.error('Load ledger error:', err);
    }
    finally { setLoading(false); }
  }, [api, dateTo]);

  // Load detailed entries for a specific account
  const loadAccountDetails = useCallback(async (accountCode) => {
    if (accountDetails[accountCode]) return;  // Already loaded
    
    setLoadingDetails(prev => ({ ...prev, [accountCode]: true }));
    try {
      const params = new URLSearchParams({
        account_code: accountCode,
        ...(dateFrom && { date_from: dateFrom }),
        ...(dateTo && { date_to: dateTo })
      });
      const res = await api(`/api/accounting/financial/general-ledger?${params}`);
      if (res.ok) {
        const data = await res.json();
        setAccountDetails(prev => ({
          ...prev,
          [accountCode]: {
            entries: data.entries || [],
            summary: data.summary || {}
          }
        }));
      }
    } catch (err) { 
      console.error('Load account details error:', err);
      toast.error('Gagal memuat detail akun');
    }
    finally { 
      setLoadingDetails(prev => ({ ...prev, [accountCode]: false })); 
    }
  }, [api, dateFrom, dateTo, accountDetails]);

  useEffect(() => { 
    loadLedger(); 
  }, [loadLedger]);

  const toggleExpand = async (accountCode) => {
    const newState = !expandedAccounts[accountCode];
    setExpandedAccounts(prev => ({
      ...prev,
      [accountCode]: newState
    }));
    
    // Load details when expanding
    if (newState) {
      await loadAccountDetails(accountCode);
    }
  };

  const exportToExcel = () => {
    toast.info('Export Excel akan segera tersedia');
  };

  const getAccountEntries = (accountCode) => {
    return accountDetails[accountCode]?.entries || [];
  };

  return (
    <div className="space-y-4" data-testid="general-ledger-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Buku Besar</h1>
          <p className="text-gray-400 text-sm">General Ledger - Riwayat transaksi per akun</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={loadLedger} 
            className="px-4 py-2 bg-amber-600/20 text-amber-400 rounded-lg flex items-center gap-2 hover:bg-amber-600/30"
            data-testid="refresh-ledger-btn"
          >
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
          <button onClick={exportToExcel} className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg flex items-center gap-2 hover:bg-green-600/30">
            <Download className="h-4 w-4" /> Export
          </button>
          <button className="px-4 py-2 bg-blue-600/20 text-blue-400 rounded-lg flex items-center gap-2 hover:bg-blue-600/30">
            <Printer className="h-4 w-4" /> Cetak
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Dari Tanggal</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
              data-testid="date-from-filter" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sampai Tanggal</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
              data-testid="date-to-filter" />
          </div>
        </div>
      </div>

      {/* Ledger Cards */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
            <p className="text-gray-400 mt-2">Memuat data buku besar...</p>
          </div>
        ) : ledgerData.length === 0 ? (
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 text-center text-gray-400">
            Belum ada data buku besar
          </div>
        ) : ledgerData.map(account => (
          <div key={account.account_code} className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden" data-testid={`ledger-account-${account.account_code}`}>
            <button
              onClick={() => toggleExpand(account.account_code)}
              className="w-full p-4 flex items-center justify-between hover:bg-red-900/10 transition-colors"
              data-testid={`expand-btn-${account.account_code}`}
            >
              <div className="flex items-center gap-3">
                {expandedAccounts[account.account_code] ? 
                  <ChevronDown className="h-5 w-5 text-amber-400" /> : 
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                }
                <FileText className="h-5 w-5 text-gray-500" />
                <div className="text-left">
                  <span className="font-mono text-amber-300">{account.account_code}</span>
                  <span className="mx-2 text-gray-500">-</span>
                  <span className="font-medium text-gray-200">{account.account_name}</span>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-xs text-gray-400">Debit</p>
                  <p className="font-medium text-blue-400">Rp {(account.total_debit || 0).toLocaleString('id-ID')}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-400">Kredit</p>
                  <p className="font-medium text-green-400">Rp {(account.total_credit || 0).toLocaleString('id-ID')}</p>
                </div>
                <div className="text-right min-w-[140px]">
                  <p className="text-xs text-gray-400">Saldo</p>
                  <p className={`font-bold ${account.balance >= 0 ? 'text-amber-200' : 'text-red-400'}`}>
                    Rp {Math.abs(account.balance || 0).toLocaleString('id-ID')}
                  </p>
                </div>
              </div>
            </button>
            
            {expandedAccounts[account.account_code] && (
              <div className="border-t border-red-900/30">
                {loadingDetails[account.account_code] ? (
                  <div className="p-4 text-center">
                    <Loader2 className="h-5 w-5 animate-spin mx-auto text-amber-400" />
                    <p className="text-sm text-gray-400 mt-1">Memuat detail...</p>
                  </div>
                ) : getAccountEntries(account.account_code).length === 0 ? (
                  <div className="p-4 text-center text-gray-400 text-sm">
                    Tidak ada transaksi untuk akun ini
                  </div>
                ) : (
                  <table className="w-full">
                    <thead className="bg-red-900/10">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs text-gray-400">TANGGAL</th>
                        <th className="px-4 py-2 text-left text-xs text-gray-400">NO. JURNAL</th>
                        <th className="px-4 py-2 text-left text-xs text-gray-400">KETERANGAN</th>
                        <th className="px-4 py-2 text-right text-xs text-gray-400">DEBIT</th>
                        <th className="px-4 py-2 text-right text-xs text-gray-400">KREDIT</th>
                        <th className="px-4 py-2 text-right text-xs text-gray-400">SALDO</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-red-900/20">
                      {getAccountEntries(account.account_code).map((entry, idx) => (
                        <tr key={idx} className="hover:bg-red-900/5" data-testid={`entry-row-${idx}`}>
                          <td className="px-4 py-2 text-sm text-gray-400">
                            {entry.date ? new Date(entry.date).toLocaleDateString('id-ID') : '-'}
                          </td>
                          <td className="px-4 py-2 text-sm font-mono text-amber-300">{entry.journal_number || '-'}</td>
                          <td className="px-4 py-2 text-sm text-gray-300">{entry.description || '-'}</td>
                          <td className="px-4 py-2 text-sm text-right text-blue-400">
                            {entry.debit > 0 ? `Rp ${entry.debit.toLocaleString('id-ID')}` : '-'}
                          </td>
                          <td className="px-4 py-2 text-sm text-right text-green-400">
                            {entry.credit > 0 ? `Rp ${entry.credit.toLocaleString('id-ID')}` : '-'}
                          </td>
                          <td className="px-4 py-2 text-sm text-right text-amber-200">
                            {entry.running_balance !== undefined ? `Rp ${entry.running_balance.toLocaleString('id-ID')}` : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Summary */}
      {!loading && ledgerData.length > 0 && (
        <div className="bg-[#1a1214] border border-amber-600/30 rounded-xl p-4">
          <div className="flex justify-between items-center">
            <span className="text-gray-400">Total Akun: {ledgerData.length}</span>
            <div className="flex gap-8">
              <div className="text-right">
                <span className="text-xs text-gray-400">Total Debit</span>
                <p className="font-bold text-blue-400">
                  Rp {ledgerData.reduce((sum, a) => sum + (a.total_debit || 0), 0).toLocaleString('id-ID')}
                </p>
              </div>
              <div className="text-right">
                <span className="text-xs text-gray-400">Total Kredit</span>
                <p className="font-bold text-green-400">
                  Rp {ledgerData.reduce((sum, a) => sum + (a.total_credit || 0), 0).toLocaleString('id-ID')}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GeneralLedger;
