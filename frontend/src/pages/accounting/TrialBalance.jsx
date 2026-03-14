import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Download, Printer, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';

const TrialBalance = () => {
  const { api } = useAuth();
  const [data, setData] = useState({ accounts: [], items: [], total_debit: 0, total_credit: 0, totals: { debit: 0, credit: 0, is_balanced: true }, is_balanced: true });
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Use the unified financial trial-balance endpoint
      const params = new URLSearchParams();
      if (dateTo) {
        params.append('date', dateTo);
      }
      const res = await api(`/api/accounting/financial/trial-balance?${params}`);
      if (res.ok) {
        setData(await res.json());
      }
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, dateTo]);

  useEffect(() => { loadData(); }, [loadData]);

  const categories = {
    asset: 'Aset',
    liability: 'Kewajiban',
    equity: 'Modal',
    revenue: 'Pendapatan',
    expense: 'Beban'
  };

  // Handle both old (items) and new (accounts) API response format
  const items = data.accounts || data.items || [];
  const totalDebit = data.totals?.debit || data.total_debit || 0;
  const totalCredit = data.totals?.credit || data.total_credit || 0;
  const isBalanced = data.totals?.is_balanced ?? data.is_balanced ?? true;

  const groupedItems = items.reduce((acc, item) => {
    // Map account_type to category if category not present
    const cat = item.category || item.account_type || 'other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {});

  return (
    <div className="space-y-4" data-testid="trial-balance-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Neraca Saldo</h1>
          <p className="text-gray-400 text-sm">Trial Balance - Ringkasan saldo semua akun</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg flex items-center gap-2">
            <Download className="h-4 w-4" /> Export
          </button>
          <button className="px-4 py-2 bg-blue-600/20 text-blue-400 rounded-lg flex items-center gap-2">
            <Printer className="h-4 w-4" /> Cetak
          </button>
        </div>
      </div>

      {/* Status Card */}
      <div className={`p-4 rounded-xl flex items-center justify-between ${
        isBalanced ? 'bg-green-600/10 border border-green-600/30' : 'bg-red-600/10 border border-red-600/30'
      }`}>
        <div className="flex items-center gap-3">
          {isBalanced ? 
            <CheckCircle className="h-6 w-6 text-green-400" /> : 
            <XCircle className="h-6 w-6 text-red-400" />
          }
          <span className={isBalanced ? 'text-green-400' : 'text-red-400'}>
            {isBalanced ? 'Neraca Seimbang' : 'Neraca Tidak Seimbang'}
          </span>
        </div>
        <div className="flex gap-8">
          <div className="text-right">
            <p className="text-sm text-gray-400">Total Debit</p>
            <p className="text-xl font-bold text-blue-400">Rp {totalDebit.toLocaleString('id-ID')}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-400">Total Kredit</p>
            <p className="text-xl font-bold text-green-400">Rp {totalCredit.toLocaleString('id-ID')}</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" placeholder="Dari" />
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" placeholder="Sampai" />
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></div>
        ) : (
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA AKUN</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">DEBIT</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">KREDIT</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(groupedItems).map(([category, items]) => (
                <React.Fragment key={category}>
                  <tr className="bg-red-900/10">
                    <td colSpan={4} className="px-4 py-2 font-semibold text-amber-200">
                      {categories[category] || category}
                    </td>
                  </tr>
                  {items.map((item, idx) => (
                    <tr key={idx} className="border-t border-red-900/20 hover:bg-red-900/5">
                      <td className="px-4 py-3 text-sm font-mono text-amber-300 pl-8">{item.account_code}</td>
                      <td className="px-4 py-3 text-sm text-gray-200">{item.account_name}</td>
                      <td className="px-4 py-3 text-sm text-right text-blue-400">
                        {(item.debit_balance || item.debit || 0) > 0 ? `Rp ${(item.debit_balance || item.debit).toLocaleString('id-ID')}` : '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-right text-green-400">
                        {(item.credit_balance || item.credit || 0) > 0 ? `Rp ${(item.credit_balance || item.credit).toLocaleString('id-ID')}` : '-'}
                      </td>
                    </tr>
                  ))}
                </React.Fragment>
              ))}
              <tr className="bg-red-900/20 font-bold">
                <td colSpan={2} className="px-4 py-3 text-amber-200">TOTAL</td>
                <td className="px-4 py-3 text-right text-blue-400">Rp {totalDebit.toLocaleString('id-ID')}</td>
                <td className="px-4 py-3 text-right text-green-400">Rp {totalCredit.toLocaleString('id-ID')}</td>
              </tr>
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default TrialBalance;
