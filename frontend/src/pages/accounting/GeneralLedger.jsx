import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Search, Download, Printer, Loader2, FileText, ChevronDown, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { getDefaultFilterDates, formatDateDisplay } from '../../utils/dateUtils';

const GeneralLedger = () => {
  const { api } = useAuth();
  const [ledger, setLedger] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { dateFrom: defaultFrom, dateTo: defaultTo } = getDefaultFilterDates();
  const [dateFrom, setDateFrom] = useState(defaultFrom);
  const [dateTo, setDateTo] = useState(defaultTo);
  const [accountFilter, setAccountFilter] = useState('');
  const [expandedAccounts, setExpandedAccounts] = useState({});

  const loadLedger = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(dateFrom && { date_from: dateFrom }),
        ...(dateTo && { date_to: dateTo }),
        ...(accountFilter && { account_id: accountFilter })
      });
      const res = await api(`/api/accounting/ledger?${params}`);
      if (res.ok) {
        const data = await res.json();
        setLedger(data.items || []);
      }
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, dateFrom, dateTo, accountFilter]);

  const loadAccounts = useCallback(async () => {
    try {
      const res = await api('/api/accounting/accounts?include_inactive=false');
      if (res.ok) {
        const data = await res.json();
        setAccounts(data.items || []);
      }
    } catch (err) { console.error('Error loading accounts'); }
  }, [api]);

  useEffect(() => { 
    loadLedger(); 
    loadAccounts();
  }, [loadLedger, loadAccounts]);

  const toggleExpand = (accountId) => {
    setExpandedAccounts(prev => ({
      ...prev,
      [accountId]: !prev[accountId]
    }));
  };

  const exportToExcel = () => {
    toast.info('Export Excel akan segera tersedia');
  };

  return (
    <div className="space-y-4" data-testid="general-ledger-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Buku Besar</h1>
          <p className="text-gray-400 text-sm">General Ledger - Riwayat transaksi per akun</p>
        </div>
        <div className="flex gap-2">
          <button onClick={exportToExcel} className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg flex items-center gap-2">
            <Download className="h-4 w-4" /> Export
          </button>
          <button className="px-4 py-2 bg-blue-600/20 text-blue-400 rounded-lg flex items-center gap-2">
            <Printer className="h-4 w-4" /> Cetak
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select value={accountFilter} onChange={(e) => setAccountFilter(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200">
            <option value="">Semua Akun</option>
            {accounts.map(a => (
              <option key={a.id} value={a.id}>{a.code} - {a.name}</option>
            ))}
          </select>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
        </div>
      </div>

      {/* Ledger Cards */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
          </div>
        ) : ledger.length === 0 ? (
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 text-center text-gray-400">
            Belum ada data buku besar
          </div>
        ) : ledger.map(account => (
          <div key={account.account_id} className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
            <button
              onClick={() => toggleExpand(account.account_id)}
              className="w-full p-4 flex items-center justify-between hover:bg-red-900/10"
            >
              <div className="flex items-center gap-3">
                {expandedAccounts[account.account_id] ? 
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
                <div className="text-right min-w-[120px]">
                  <p className="text-xs text-gray-400">Saldo</p>
                  <p className={`font-bold ${account.balance >= 0 ? 'text-amber-200' : 'text-red-400'}`}>
                    Rp {Math.abs(account.balance || 0).toLocaleString('id-ID')}
                  </p>
                </div>
              </div>
            </button>
            
            {expandedAccounts[account.account_id] && (
              <div className="border-t border-red-900/30">
                <table className="w-full">
                  <thead className="bg-red-900/10">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs text-gray-400">TANGGAL</th>
                      <th className="px-4 py-2 text-left text-xs text-gray-400">NO. JURNAL</th>
                      <th className="px-4 py-2 text-left text-xs text-gray-400">KETERANGAN</th>
                      <th className="px-4 py-2 text-right text-xs text-gray-400">DEBIT</th>
                      <th className="px-4 py-2 text-right text-xs text-gray-400">KREDIT</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-900/20">
                    {account.entries?.map((entry, idx) => (
                      <tr key={idx} className="hover:bg-red-900/5">
                        <td className="px-4 py-2 text-sm text-gray-400">
                          {new Date(entry.date).toLocaleDateString('id-ID')}
                        </td>
                        <td className="px-4 py-2 text-sm font-mono text-amber-300">{entry.journal_number}</td>
                        <td className="px-4 py-2 text-sm text-gray-300">{entry.description}</td>
                        <td className="px-4 py-2 text-sm text-right text-blue-400">
                          {entry.debit > 0 ? `Rp ${entry.debit.toLocaleString('id-ID')}` : '-'}
                        </td>
                        <td className="px-4 py-2 text-sm text-right text-green-400">
                          {entry.credit > 0 ? `Rp ${entry.credit.toLocaleString('id-ID')}` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default GeneralLedger;
