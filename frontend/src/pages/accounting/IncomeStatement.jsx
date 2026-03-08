import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Download, Printer, Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { toast } from 'sonner';

const IncomeStatement = () => {
  const { api } = useAuth();
  const [data, setData] = useState({ revenues: [], expenses: [], total_revenue: 0, total_expense: 0, net_income: 0 });
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState(new Date().getFullYear() + '-01-01');
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        date_from: dateFrom,
        date_to: dateTo
      });
      const res = await api(`/api/accounting/financial/income-statement?${params}`);
      if (res.ok) {
        setData(await res.json());
      }
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, dateFrom, dateTo]);

  useEffect(() => { loadData(); }, [loadData]);

  return (
    <div className="space-y-4" data-testid="income-statement-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Laporan Laba Rugi</h1>
          <p className="text-gray-400 text-sm">Income Statement - Periode {dateFrom} s/d {dateTo}</p>
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

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-[#1a1214] border border-green-600/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-5 w-5 text-green-400" />
            <p className="text-gray-400 text-sm">Total Pendapatan</p>
          </div>
          <p className="text-2xl font-bold text-green-400">Rp {data.total_revenue.toLocaleString('id-ID')}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-600/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="h-5 w-5 text-red-400" />
            <p className="text-gray-400 text-sm">Total Beban</p>
          </div>
          <p className="text-2xl font-bold text-red-400">Rp {data.total_expense.toLocaleString('id-ID')}</p>
        </div>
        <div className={`bg-[#1a1214] border rounded-xl p-4 ${data.net_income >= 0 ? 'border-amber-600/30' : 'border-red-600/30'}`}>
          <div className="flex items-center gap-2 mb-2">
            {data.net_income >= 0 ? <TrendingUp className="h-5 w-5 text-amber-400" /> : <TrendingDown className="h-5 w-5 text-red-400" />}
            <p className="text-gray-400 text-sm">{data.net_income >= 0 ? 'Laba Bersih' : 'Rugi Bersih'}</p>
          </div>
          <p className={`text-2xl font-bold ${data.net_income >= 0 ? 'text-amber-400' : 'text-red-400'}`}>
            Rp {Math.abs(data.net_income).toLocaleString('id-ID')}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Dari Tanggal</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Sampai Tanggal</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
          </div>
        </div>
      </div>

      {/* Report Content */}
      {loading ? (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
        </div>
      ) : (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          {/* Revenues */}
          <div className="p-4 border-b border-red-900/30">
            <h3 className="text-lg font-semibold text-green-400 mb-4">PENDAPATAN</h3>
            <table className="w-full">
              <tbody>
                {data.revenues.length === 0 ? (
                  <tr><td className="py-2 text-gray-400">Belum ada data pendapatan</td></tr>
                ) : data.revenues.map((item, idx) => (
                  <tr key={idx} className="border-b border-red-900/10">
                    <td className="py-2 text-gray-300 pl-4">{item.account_code} - {item.account_name}</td>
                    <td className="py-2 text-right text-green-400">Rp {item.amount.toLocaleString('id-ID')}</td>
                  </tr>
                ))}
                <tr className="font-bold">
                  <td className="py-3 text-amber-200">Total Pendapatan</td>
                  <td className="py-3 text-right text-green-400">Rp {data.total_revenue.toLocaleString('id-ID')}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Expenses */}
          <div className="p-4 border-b border-red-900/30">
            <h3 className="text-lg font-semibold text-red-400 mb-4">BEBAN</h3>
            <table className="w-full">
              <tbody>
                {data.expenses.length === 0 ? (
                  <tr><td className="py-2 text-gray-400">Belum ada data beban</td></tr>
                ) : data.expenses.map((item, idx) => (
                  <tr key={idx} className="border-b border-red-900/10">
                    <td className="py-2 text-gray-300 pl-4">{item.account_code} - {item.account_name}</td>
                    <td className="py-2 text-right text-red-400">Rp {item.amount.toLocaleString('id-ID')}</td>
                  </tr>
                ))}
                <tr className="font-bold">
                  <td className="py-3 text-amber-200">Total Beban</td>
                  <td className="py-3 text-right text-red-400">Rp {data.total_expense.toLocaleString('id-ID')}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Net Income */}
          <div className="p-4 bg-red-900/20">
            <table className="w-full">
              <tbody>
                <tr className="font-bold text-xl">
                  <td className="py-3 text-amber-100">{data.net_income >= 0 ? 'LABA BERSIH' : 'RUGI BERSIH'}</td>
                  <td className={`py-3 text-right ${data.net_income >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    Rp {Math.abs(data.net_income).toLocaleString('id-ID')}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default IncomeStatement;
