import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Calculator, BookOpen, FileText, TrendingUp, TrendingDown, Loader2, Download, Calendar } from 'lucide-react';
import { toast } from 'sonner';

const Accounting = () => {
  const { api, user } = useAuth();
  const [activeTab, setActiveTab] = useState('profit-loss');
  const [loading, setLoading] = useState(true);
  const [profitLoss, setProfitLoss] = useState(null);
  const [dateFrom, setDateFrom] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().slice(0, 10));
  const [dateTo, setDateTo] = useState(new Date().toISOString().slice(0, 10));

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  useEffect(() => {
    if (activeTab === 'profit-loss') loadProfitLoss();
  }, [activeTab, dateFrom, dateTo]);

  const loadProfitLoss = async () => {
    setLoading(true);
    try {
      const res = await api(`/api/finance/reports/profit-loss?date_from=${dateFrom}&date_to=${dateTo}`);
      if (res.ok) setProfitLoss(await res.json());
    } catch (err) { toast.error('Gagal memuat laporan'); }
    finally { setLoading(false); }
  };

  const tabs = [
    { id: 'profit-loss', label: 'Laba Rugi', icon: TrendingUp },
    { id: 'balance', label: 'Neraca', icon: BookOpen },
    { id: 'journal', label: 'Jurnal', icon: FileText }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Akuntansi</h1>
          <p className="text-gray-400">Laporan keuangan perusahaan</p>
        </div>
        <div className="flex gap-2 items-center">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm" />
            <span className="text-gray-400">-</span>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm" />
          </div>
        </div>
      </div>

      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${activeTab === tab.id ? 'bg-red-900/30 text-amber-400' : 'text-gray-400 hover:text-white hover:bg-red-900/20'}`}>
            <tab.icon className="h-4 w-4" /> {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Laba Rugi */}
      {activeTab === 'profit-loss' && (
        loading ? (
          <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-red-400" /></div>
        ) : profitLoss ? (
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-amber-100">Laporan Laba Rugi</h2>
              <div className="text-sm text-gray-400">
                Periode: {new Date(dateFrom).toLocaleDateString('id-ID')} - {new Date(dateTo).toLocaleDateString('id-ID')}
              </div>
            </div>

            <div className="space-y-6">
              {/* Pendapatan */}
              <div>
                <h3 className="text-lg font-semibold text-green-400 mb-3 border-b border-green-900/30 pb-2">PENDAPATAN</h3>
                <div className="space-y-2 pl-4">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Penjualan Kotor</span>
                    <span>{formatRupiah(profitLoss.revenue?.gross_sales)}</span>
                  </div>
                  <div className="flex justify-between text-red-400">
                    <span>Diskon Penjualan</span>
                    <span>({formatRupiah(profitLoss.revenue?.discounts)})</span>
                  </div>
                  <div className="flex justify-between font-semibold border-t border-red-900/20 pt-2">
                    <span>Penjualan Bersih</span>
                    <span className="text-green-400">{formatRupiah(profitLoss.revenue?.net_sales)}</span>
                  </div>
                </div>
              </div>

              {/* HPP */}
              <div>
                <h3 className="text-lg font-semibold text-amber-400 mb-3 border-b border-amber-900/30 pb-2">HARGA POKOK PENJUALAN</h3>
                <div className="space-y-2 pl-4">
                  <div className="flex justify-between font-semibold">
                    <span>Total HPP</span>
                    <span className="text-red-400">({formatRupiah(profitLoss.cost_of_goods_sold)})</span>
                  </div>
                </div>
              </div>

              {/* Laba Kotor */}
              <div className="bg-green-900/10 border border-green-900/30 rounded-lg p-4">
                <div className="flex justify-between text-lg font-bold">
                  <span className="text-green-400">LABA KOTOR</span>
                  <span className="text-green-400">{formatRupiah(profitLoss.gross_profit)}</span>
                </div>
              </div>

              {/* Beban Operasional */}
              <div>
                <h3 className="text-lg font-semibold text-red-400 mb-3 border-b border-red-900/30 pb-2">BEBAN OPERASIONAL</h3>
                <div className="space-y-2 pl-4">
                  {profitLoss.operating_expenses?.breakdown?.map((exp, idx) => (
                    <div key={idx} className="flex justify-between">
                      <span className="text-gray-400">{exp.category}</span>
                      <span className="text-red-400">({formatRupiah(exp.amount)})</span>
                    </div>
                  ))}
                  <div className="flex justify-between font-semibold border-t border-red-900/20 pt-2">
                    <span>Total Beban Operasional</span>
                    <span className="text-red-400">({formatRupiah(profitLoss.operating_expenses?.total)})</span>
                  </div>
                </div>
              </div>

              {/* Laba Bersih */}
              <div className={`border rounded-lg p-4 ${profitLoss.net_profit >= 0 ? 'bg-green-900/20 border-green-700/50' : 'bg-red-900/20 border-red-700/50'}`}>
                <div className="flex justify-between text-xl font-bold">
                  <span className={profitLoss.net_profit >= 0 ? 'text-green-400' : 'text-red-400'}>LABA BERSIH</span>
                  <span className={profitLoss.net_profit >= 0 ? 'text-green-400' : 'text-red-400'}>{formatRupiah(profitLoss.net_profit)}</span>
                </div>
                <div className="text-sm text-gray-400 mt-1">
                  Margin: {profitLoss.profit_margin?.toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">Tidak ada data untuk periode ini</div>
        )
      )}

      {/* Tab Neraca */}
      {activeTab === 'balance' && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
          <h2 className="text-xl font-bold text-amber-100 mb-6">Neraca</h2>
          <div className="grid grid-cols-2 gap-6">
            {/* Aset */}
            <div>
              <h3 className="text-lg font-semibold text-green-400 mb-4 border-b border-green-900/30 pb-2">ASET</h3>
              <div className="space-y-4">
                <div>
                  <div className="text-gray-400 text-sm mb-2">Aset Lancar</div>
                  <div className="space-y-2 pl-4">
                    <div className="flex justify-between">
                      <span>Kas</span>
                      <span>{formatRupiah(0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Piutang Usaha</span>
                      <span>{formatRupiah(0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Persediaan</span>
                      <span>{formatRupiah(0)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex justify-between font-bold pt-2 border-t border-red-900/30">
                  <span>TOTAL ASET</span>
                  <span className="text-green-400">{formatRupiah(0)}</span>
                </div>
              </div>
            </div>

            {/* Kewajiban & Ekuitas */}
            <div>
              <h3 className="text-lg font-semibold text-red-400 mb-4 border-b border-red-900/30 pb-2">KEWAJIBAN & EKUITAS</h3>
              <div className="space-y-4">
                <div>
                  <div className="text-gray-400 text-sm mb-2">Kewajiban</div>
                  <div className="space-y-2 pl-4">
                    <div className="flex justify-between">
                      <span>Hutang Usaha</span>
                      <span>{formatRupiah(0)}</span>
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-gray-400 text-sm mb-2">Ekuitas</div>
                  <div className="space-y-2 pl-4">
                    <div className="flex justify-between">
                      <span>Modal</span>
                      <span>{formatRupiah(0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Laba Ditahan</span>
                      <span>{formatRupiah(0)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex justify-between font-bold pt-2 border-t border-red-900/30">
                  <span>TOTAL KEWAJIBAN & EKUITAS</span>
                  <span className="text-green-400">{formatRupiah(0)}</span>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-6 p-4 bg-amber-900/10 border border-amber-700/30 rounded-lg">
            <p className="text-amber-400 text-sm">Catatan: Laporan neraca dalam pengembangan. Data akan otomatis terintegrasi dengan transaksi.</p>
          </div>
        </div>
      )}

      {/* Tab Jurnal */}
      {activeTab === 'journal' && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
          <h2 className="text-xl font-bold text-amber-100 mb-6">Jurnal Umum</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-red-900/20">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Tanggal</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">No. Ref</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Keterangan</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Debet</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Kredit</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                    <Calculator className="h-12 w-12 mx-auto mb-2 opacity-30" />
                    <p>Jurnal otomatis dalam pengembangan</p>
                    <p className="text-sm">Setiap transaksi akan tercatat sebagai jurnal</p>
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

export default Accounting;
