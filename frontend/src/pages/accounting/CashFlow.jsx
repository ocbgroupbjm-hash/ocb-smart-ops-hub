import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Download, Printer, Loader2, TrendingUp, TrendingDown, ArrowRight, Wallet, Building2, Briefcase } from 'lucide-react';
import { toast } from 'sonner';

const CashFlow = () => {
  const { api } = useAuth();
  const [data, setData] = useState({ 
    operating: { items: [], total: 0 },
    investing: { items: [], total: 0 },
    financing: { items: [], total: 0 },
    net_cash_flow: 0
  });
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
      const res = await api(`/api/accounting/financial/cash-flow?${params}`);
      if (res.ok) {
        setData(await res.json());
      }
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, dateFrom, dateTo]);

  useEffect(() => { loadData(); }, [loadData]);

  const FlowSection = ({ title, icon: Icon, items, total, color }) => (
    <div className={`bg-[#1a1214] border border-${color}-600/30 rounded-xl overflow-hidden`}>
      <div className={`p-4 bg-${color}-600/10 border-b border-${color}-600/30 flex items-center gap-2`}>
        <Icon className={`h-5 w-5 text-${color}-400`} />
        <h3 className={`text-lg font-semibold text-${color}-400`}>{title}</h3>
      </div>
      <div className="p-4">
        {items.length === 0 ? (
          <p className="text-gray-400 text-center py-4">Belum ada data</p>
        ) : (
          <table className="w-full">
            <tbody>
              {items.map((item, idx) => (
                <tr key={idx} className={`border-b border-${color}-600/10`}>
                  <td className="py-2 text-sm text-gray-400">{new Date(item.date).toLocaleDateString('id-ID')}</td>
                  <td className="py-2 text-gray-300">{item.description}</td>
                  <td className={`py-2 text-right ${item.amount >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {item.amount >= 0 ? '+' : ''}Rp {Math.abs(item.amount).toLocaleString('id-ID')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <div className={`p-4 bg-${color}-600/10 border-t border-${color}-600/30`}>
        <div className="flex justify-between font-bold">
          <span className={`text-${color}-200`}>Total</span>
          <span className={total >= 0 ? 'text-green-400' : 'text-red-400'}>
            {total >= 0 ? '+' : ''}Rp {Math.abs(total).toLocaleString('id-ID')}
          </span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-4" data-testid="cash-flow-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Laporan Arus Kas</h1>
          <p className="text-gray-400 text-sm">Cash Flow Statement - Periode {dateFrom} s/d {dateTo}</p>
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

      {/* Summary Card */}
      <div className={`p-6 rounded-xl ${data.net_cash_flow >= 0 ? 'bg-green-600/10 border border-green-600/30' : 'bg-red-600/10 border border-red-600/30'}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {data.net_cash_flow >= 0 ? 
              <TrendingUp className="h-8 w-8 text-green-400" /> : 
              <TrendingDown className="h-8 w-8 text-red-400" />
            }
            <div>
              <p className="text-gray-400 text-sm">Arus Kas Bersih</p>
              <p className={`text-3xl font-bold ${data.net_cash_flow >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {data.net_cash_flow >= 0 ? '+' : ''}Rp {Math.abs(data.net_cash_flow).toLocaleString('id-ID')}
              </p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="text-center">
              <p className="text-xs text-gray-400">Operasional</p>
              <p className={`text-lg font-bold ${data.operating.total >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                Rp {Math.abs(data.operating.total).toLocaleString('id-ID')}
              </p>
            </div>
            <ArrowRight className="h-6 w-6 text-gray-500 self-center" />
            <div className="text-center">
              <p className="text-xs text-gray-400">Investasi</p>
              <p className={`text-lg font-bold ${data.investing.total >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                Rp {Math.abs(data.investing.total).toLocaleString('id-ID')}
              </p>
            </div>
            <ArrowRight className="h-6 w-6 text-gray-500 self-center" />
            <div className="text-center">
              <p className="text-xs text-gray-400">Pendanaan</p>
              <p className={`text-lg font-bold ${data.financing.total >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                Rp {Math.abs(data.financing.total).toLocaleString('id-ID')}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Date Filters */}
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

      {loading ? (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <FlowSection 
            title="Arus Kas Operasional" 
            icon={Wallet} 
            items={data.operating.items} 
            total={data.operating.total}
            color="blue"
          />
          <FlowSection 
            title="Arus Kas Investasi" 
            icon={Building2} 
            items={data.investing.items} 
            total={data.investing.total}
            color="purple"
          />
          <FlowSection 
            title="Arus Kas Pendanaan" 
            icon={Briefcase} 
            items={data.financing.items} 
            total={data.financing.total}
            color="amber"
          />
        </div>
      )}
    </div>
  );
};

export default CashFlow;
