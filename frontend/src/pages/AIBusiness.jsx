import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Brain, TrendingUp, TrendingDown, Package, AlertTriangle, Building2, ShoppingCart, Lightbulb, RefreshCw, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const AIBusiness = () => {
  const { api, user } = useAuth();
  const [activeTab, setActiveTab] = useState('insight');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => { loadData(); }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      let endpoint = '';
      switch (activeTab) {
        case 'insight': endpoint = '/api/ai-bisnis/insight-penjualan'; break;
        case 'restock': endpoint = '/api/ai-bisnis/rekomendasi-restock'; break;
        case 'terlaris': endpoint = '/api/ai-bisnis/produk-terlaris'; break;
        case 'lambat': endpoint = '/api/ai-bisnis/produk-lambat'; break;
        case 'stok': endpoint = '/api/ai-bisnis/analisa-stok'; break;
        case 'cabang': endpoint = '/api/ai-bisnis/performa-cabang'; break;
        case 'rekomendasi': endpoint = '/api/ai-bisnis/rekomendasi-bisnis'; break;
        default: return;
      }
      const res = await api(endpoint);
      if (res.ok) setData(await res.json());
      else toast.error('Gagal memuat data');
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  };

  const refresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
    toast.success('Data diperbarui');
  };

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  const tabs = [
    { id: 'insight', label: 'Insight Penjualan', icon: TrendingUp },
    { id: 'restock', label: 'Rekomendasi Restock', icon: ShoppingCart },
    { id: 'terlaris', label: 'Produk Terlaris', icon: Package },
    { id: 'lambat', label: 'Produk Lambat', icon: AlertTriangle },
    { id: 'stok', label: 'Analisa Stok', icon: Package },
    ...(user?.role === 'owner' || user?.role === 'admin' ? [{ id: 'cabang', label: 'Performa Cabang', icon: Building2 }] : []),
    { id: 'rekomendasi', label: 'Rekomendasi Bisnis', icon: Lightbulb }
  ];

  const renderInsightBadge = (insight) => {
    const colors = {
      positive: 'bg-green-900/30 text-green-400 border-green-700/30',
      warning: 'bg-amber-900/30 text-amber-400 border-amber-700/30',
      info: 'bg-blue-900/30 text-blue-400 border-blue-700/30'
    };
    return (
      <div key={insight.message} className={`p-3 rounded-lg border ${colors[insight.type] || colors.info}`}>
        {insight.message}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-br from-purple-600/20 to-blue-600/20 rounded-xl">
            <Brain className="h-8 w-8 text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-amber-100">AI Bisnis</h1>
            <p className="text-gray-400">Analisis cerdas untuk keputusan bisnis</p>
          </div>
        </div>
        <button onClick={refresh} disabled={refreshing} className="px-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg flex items-center gap-2 hover:bg-red-900/20">
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Perbarui
        </button>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-red-900/30 pb-2">
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${activeTab === tab.id ? 'bg-red-900/30 text-amber-400' : 'text-gray-400 hover:text-white hover:bg-red-900/20'}`}>
            <tab.icon className="h-4 w-4" /> {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-red-400" /></div>
      ) : data ? (
        <>
          {/* Tab Insight Penjualan */}
          {activeTab === 'insight' && (
            <div className="space-y-6">
              <div className="text-sm text-gray-400">Periode: {data.periode}</div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Penjualan</div>
                  <div className="text-2xl font-bold text-green-400">{formatRupiah(data.ringkasan?.total_penjualan)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Laba</div>
                  <div className="text-2xl font-bold text-amber-400">{formatRupiah(data.ringkasan?.total_laba)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Pertumbuhan Penjualan</div>
                  <div className={`text-2xl font-bold flex items-center gap-2 ${data.ringkasan?.pertumbuhan_penjualan >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {data.ringkasan?.pertumbuhan_penjualan >= 0 ? <TrendingUp className="h-6 w-6" /> : <TrendingDown className="h-6 w-6" />}
                    {data.ringkasan?.pertumbuhan_penjualan?.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Rata-rata Transaksi</div>
                  <div className="text-2xl font-bold">{formatRupiah(data.ringkasan?.rata_rata_transaksi)}</div>
                </div>
              </div>
              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><Brain className="h-5 w-5 text-purple-400" /> AI Insights</h3>
                <div className="space-y-3">
                  {data.insights?.map(renderInsightBadge)}
                </div>
              </div>
            </div>
          )}

          {/* Tab Rekomendasi Restock */}
          {activeTab === 'restock' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gradient-to-br from-amber-600/20 to-red-600/20 border border-amber-700/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Produk Perlu Restock</div>
                  <div className="text-3xl font-bold text-amber-400">{data.total_produk_perlu_restock}</div>
                </div>
                <div className="bg-gradient-to-br from-purple-600/20 to-blue-600/20 border border-purple-700/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Estimasi Biaya Order</div>
                  <div className="text-3xl font-bold text-purple-400">{formatRupiah(data.total_estimasi_biaya)}</div>
                </div>
              </div>
              {data.insight && <div className="p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg text-blue-400">{data.insight}</div>}
              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Stok</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Min</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Penjualan/Hari</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Order</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Biaya</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold">Urgensi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.rekomendasi?.map((item, idx) => (
                      <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                        <td className="px-4 py-3"><div className="font-medium">{item.nama_produk}</div><div className="text-xs text-gray-400">{item.kode_produk}</div></td>
                        <td className="px-4 py-3 text-right font-semibold">{item.stok_saat_ini}</td>
                        <td className="px-4 py-3 text-right text-gray-400">{item.stok_minimum}</td>
                        <td className="px-4 py-3 text-right">{item.penjualan_harian}</td>
                        <td className="px-4 py-3 text-right text-amber-400 font-semibold">{item.rekomendasi_order}</td>
                        <td className="px-4 py-3 text-right">{formatRupiah(item.estimasi_biaya)}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            item.urgensi === 'tinggi' ? 'bg-red-900/30 text-red-400' :
                            item.urgensi === 'sedang' ? 'bg-amber-900/30 text-amber-400' :
                            'bg-green-900/30 text-green-400'
                          }`}>{item.urgensi}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Produk Terlaris */}
          {activeTab === 'terlaris' && (
            <div className="space-y-6">
              <div className="text-sm text-gray-400">Periode: {data.periode}</div>
              {data.insights?.length > 0 && (
                <div className="space-y-2">
                  {data.insights.map(renderInsightBadge)}
                </div>
              )}
              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-center text-sm font-semibold w-16">#</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Terjual</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Pendapatan</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Laba</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Margin</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.produk_terlaris?.map((item) => (
                      <tr key={item.product_id} className="border-t border-red-900/10 hover:bg-red-900/10">
                        <td className="px-4 py-3 text-center">
                          <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold ${
                            item.ranking === 1 ? 'bg-amber-500 text-black' :
                            item.ranking === 2 ? 'bg-gray-400 text-black' :
                            item.ranking === 3 ? 'bg-amber-700 text-white' :
                            'bg-gray-700 text-white'
                          }`}>{item.ranking}</span>
                        </td>
                        <td className="px-4 py-3 font-medium">{item.nama_produk}</td>
                        <td className="px-4 py-3 text-right font-semibold">{item.total_terjual}</td>
                        <td className="px-4 py-3 text-right text-green-400">{formatRupiah(item.total_pendapatan)}</td>
                        <td className="px-4 py-3 text-right text-amber-400">{formatRupiah(item.total_laba)}</td>
                        <td className="px-4 py-3 text-right">{item.margin_persen}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Produk Lambat */}
          {activeTab === 'lambat' && (
            <div className="space-y-6">
              <div className="bg-gradient-to-br from-red-600/20 to-amber-600/20 border border-red-700/30 rounded-xl p-5">
                <div className="text-gray-400 mb-1">Modal Tertahan</div>
                <div className="text-3xl font-bold text-red-400">{formatRupiah(data.total_nilai_tertahan)}</div>
              </div>
              {data.insights?.length > 0 && (
                <div className="space-y-2">
                  {data.insights.map(renderInsightBadge)}
                </div>
              )}
              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Terjual</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Stok</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Nilai Stok</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Harga Jual</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.produk_lambat?.map((item, idx) => (
                      <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                        <td className="px-4 py-3"><div className="font-medium">{item.nama_produk}</div><div className="text-xs text-gray-400">{item.kode_produk}</div></td>
                        <td className="px-4 py-3 text-right text-red-400 font-semibold">{item.terjual}</td>
                        <td className="px-4 py-3 text-right">{item.stok_saat_ini}</td>
                        <td className="px-4 py-3 text-right text-amber-400">{formatRupiah(item.nilai_stok)}</td>
                        <td className="px-4 py-3 text-right">{formatRupiah(item.harga_jual)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Analisa Stok */}
          {activeTab === 'stok' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Jenis Produk</div>
                  <div className="text-2xl font-bold">{data.ringkasan?.total_jenis_produk}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Item</div>
                  <div className="text-2xl font-bold">{data.ringkasan?.total_item?.toLocaleString()}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Nilai Modal</div>
                  <div className="text-2xl font-bold text-amber-400">{formatRupiah(data.ringkasan?.nilai_modal)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Potensi Laba</div>
                  <div className="text-2xl font-bold text-green-400">{formatRupiah(data.ringkasan?.potensi_laba)}</div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-amber-900/20 border border-amber-700/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Produk Stok Menipis</div>
                  <div className="text-3xl font-bold text-amber-400">{data.ringkasan?.produk_stok_menipis}</div>
                </div>
                <div className="bg-red-900/20 border border-red-700/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Produk Habis</div>
                  <div className="text-3xl font-bold text-red-400">{data.ringkasan?.produk_habis}</div>
                </div>
              </div>
              {data.insights?.length > 0 && (
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><Brain className="h-5 w-5 text-purple-400" /> AI Insights</h3>
                  <div className="space-y-3">
                    {data.insights.map(renderInsightBadge)}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab Performa Cabang */}
          {activeTab === 'cabang' && (
            <div className="space-y-6">
              <div className="text-sm text-gray-400">Periode: {data.periode}</div>
              {data.insights?.length > 0 && (
                <div className="space-y-2">
                  {data.insights.map(renderInsightBadge)}
                </div>
              )}
              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-center text-sm font-semibold w-16">#</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Cabang</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Penjualan</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Laba</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Transaksi</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Margin</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.performa_cabang?.map((item) => (
                      <tr key={item.branch_id} className="border-t border-red-900/10 hover:bg-red-900/10">
                        <td className="px-4 py-3 text-center">
                          <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold ${
                            item.ranking === 1 ? 'bg-amber-500 text-black' :
                            item.ranking === 2 ? 'bg-gray-400 text-black' :
                            item.ranking === 3 ? 'bg-amber-700 text-white' :
                            'bg-gray-700 text-white'
                          }`}>{item.ranking}</span>
                        </td>
                        <td className="px-4 py-3"><div className="font-medium">{item.nama_cabang}</div><div className="text-xs text-gray-400">{item.kode_cabang}</div></td>
                        <td className="px-4 py-3 text-right text-green-400 font-semibold">{formatRupiah(item.total_penjualan)}</td>
                        <td className="px-4 py-3 text-right text-amber-400">{formatRupiah(item.total_laba)}</td>
                        <td className="px-4 py-3 text-right">{item.jumlah_transaksi}</td>
                        <td className="px-4 py-3 text-right">{item.margin_persen}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Rekomendasi Bisnis */}
          {activeTab === 'rekomendasi' && (
            <div className="space-y-6">
              <div className="text-sm text-gray-400">Tanggal: {data.tanggal}</div>
              <div className="bg-gradient-to-br from-purple-600/20 to-blue-600/20 border border-purple-700/30 rounded-xl p-5">
                <div className="text-gray-400 mb-1">Total Rekomendasi</div>
                <div className="text-3xl font-bold text-purple-400">{data.total_rekomendasi}</div>
              </div>
              <div className="space-y-4">
                {data.rekomendasi?.map((item, idx) => (
                  <div key={idx} className={`p-5 rounded-xl border ${
                    item.prioritas === 'tinggi' ? 'bg-red-900/10 border-red-700/30' :
                    item.prioritas === 'sedang' ? 'bg-amber-900/10 border-amber-700/30' :
                    'bg-green-900/10 border-green-700/30'
                  }`}>
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                          item.prioritas === 'tinggi' ? 'bg-red-900/30 text-red-400' :
                          item.prioritas === 'sedang' ? 'bg-amber-900/30 text-amber-400' :
                          'bg-green-900/30 text-green-400'
                        }`}>Prioritas {item.prioritas}</span>
                        <span className="ml-2 text-gray-400">{item.kategori}</span>
                      </div>
                    </div>
                    <p className="text-lg font-medium mb-3">{item.rekomendasi}</p>
                    <div className="space-y-1">
                      <div className="text-sm text-gray-400">Aksi yang disarankan:</div>
                      <ul className="list-disc list-inside text-sm space-y-1">
                        {item.aksi?.map((a, i) => <li key={i}>{a}</li>)}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12 text-gray-400">Tidak ada data</div>
      )}
    </div>
  );
};

export default AIBusiness;
