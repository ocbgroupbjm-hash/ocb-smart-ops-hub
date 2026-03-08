import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Download, Printer, Loader2, Building2, Scale, Wallet } from 'lucide-react';
import { toast } from 'sonner';

const BalanceSheet = () => {
  const { api } = useAuth();
  const [data, setData] = useState({ 
    assets: [], liabilities: [], equity: [], 
    total_assets: 0, total_liabilities: 0, total_equity: 0, is_balanced: true 
  });
  const [loading, setLoading] = useState(true);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/accounting/financial/balance-sheet?date=${date}`);
      if (res.ok) {
        setData(await res.json());
      }
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, date]);

  useEffect(() => { loadData(); }, [loadData]);

  return (
    <div className="space-y-4" data-testid="balance-sheet-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Neraca</h1>
          <p className="text-gray-400 text-sm">Balance Sheet - Per tanggal {new Date(date).toLocaleDateString('id-ID')}</p>
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

      {/* Status */}
      <div className={`p-4 rounded-xl flex items-center justify-between ${
        data.is_balanced ? 'bg-green-600/10 border border-green-600/30' : 'bg-red-600/10 border border-red-600/30'
      }`}>
        <div className="flex items-center gap-3">
          <Scale className={`h-6 w-6 ${data.is_balanced ? 'text-green-400' : 'text-red-400'}`} />
          <span className={data.is_balanced ? 'text-green-400' : 'text-red-400'}>
            {data.is_balanced ? 'Neraca Seimbang' : 'Neraca Tidak Seimbang'}
          </span>
        </div>
      </div>

      {/* Date Filter */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="max-w-xs">
          <label className="block text-sm text-gray-400 mb-1">Per Tanggal</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
            className="w-full px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
        </div>
      </div>

      {loading ? (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Assets */}
          <div className="bg-[#1a1214] border border-blue-600/30 rounded-xl overflow-hidden">
            <div className="p-4 bg-blue-600/10 border-b border-blue-600/30 flex items-center gap-2">
              <Building2 className="h-5 w-5 text-blue-400" />
              <h3 className="text-lg font-semibold text-blue-400">ASET</h3>
            </div>
            <div className="p-4">
              <table className="w-full">
                <tbody>
                  {data.assets.length === 0 ? (
                    <tr><td className="py-2 text-gray-400">Belum ada data aset</td></tr>
                  ) : data.assets.map((item, idx) => (
                    <tr key={idx} className="border-b border-blue-600/10">
                      <td className="py-2 text-gray-300">{item.account_code} - {item.account_name}</td>
                      <td className="py-2 text-right text-blue-400">Rp {(item.balance || 0).toLocaleString('id-ID')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-4 bg-blue-600/10 border-t border-blue-600/30">
              <div className="flex justify-between font-bold">
                <span className="text-blue-200">Total Aset</span>
                <span className="text-blue-400">Rp {data.total_assets.toLocaleString('id-ID')}</span>
              </div>
            </div>
          </div>

          {/* Liabilities & Equity */}
          <div className="space-y-4">
            {/* Liabilities */}
            <div className="bg-[#1a1214] border border-red-600/30 rounded-xl overflow-hidden">
              <div className="p-4 bg-red-600/10 border-b border-red-600/30 flex items-center gap-2">
                <Wallet className="h-5 w-5 text-red-400" />
                <h3 className="text-lg font-semibold text-red-400">KEWAJIBAN</h3>
              </div>
              <div className="p-4">
                <table className="w-full">
                  <tbody>
                    {data.liabilities.length === 0 ? (
                      <tr><td className="py-2 text-gray-400">Belum ada data kewajiban</td></tr>
                    ) : data.liabilities.map((item, idx) => (
                      <tr key={idx} className="border-b border-red-600/10">
                        <td className="py-2 text-gray-300">{item.account_code} - {item.account_name}</td>
                        <td className="py-2 text-right text-red-400">Rp {(item.balance || 0).toLocaleString('id-ID')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-4 bg-red-600/10 border-t border-red-600/30">
                <div className="flex justify-between font-bold">
                  <span className="text-red-200">Total Kewajiban</span>
                  <span className="text-red-400">Rp {data.total_liabilities.toLocaleString('id-ID')}</span>
                </div>
              </div>
            </div>

            {/* Equity */}
            <div className="bg-[#1a1214] border border-purple-600/30 rounded-xl overflow-hidden">
              <div className="p-4 bg-purple-600/10 border-b border-purple-600/30 flex items-center gap-2">
                <Scale className="h-5 w-5 text-purple-400" />
                <h3 className="text-lg font-semibold text-purple-400">MODAL</h3>
              </div>
              <div className="p-4">
                <table className="w-full">
                  <tbody>
                    {data.equity.length === 0 ? (
                      <tr><td className="py-2 text-gray-400">Belum ada data modal</td></tr>
                    ) : data.equity.map((item, idx) => (
                      <tr key={idx} className="border-b border-purple-600/10">
                        <td className="py-2 text-gray-300">{item.account_code} - {item.account_name}</td>
                        <td className="py-2 text-right text-purple-400">Rp {(item.balance || 0).toLocaleString('id-ID')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-4 bg-purple-600/10 border-t border-purple-600/30">
                <div className="flex justify-between font-bold">
                  <span className="text-purple-200">Total Modal</span>
                  <span className="text-purple-400">Rp {data.total_equity.toLocaleString('id-ID')}</span>
                </div>
              </div>
            </div>

            {/* Total Liabilities + Equity */}
            <div className="bg-[#1a1214] border border-amber-600/30 rounded-xl p-4">
              <div className="flex justify-between font-bold text-lg">
                <span className="text-amber-200">Total Kewajiban + Modal</span>
                <span className="text-amber-400">Rp {(data.total_liabilities + data.total_equity).toLocaleString('id-ID')}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BalanceSheet;
