import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { BarChart3, TrendingUp, Package, Users, Building2, Loader2, Download, Calendar, FileText } from 'lucide-react';
import { toast } from 'sonner';

const Reports = () => {
  const { api, user } = useAuth();
  const [activeTab, setActiveTab] = useState('sales');
  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState(null);
  const [dateFrom, setDateFrom] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().slice(0, 10));
  const [dateTo, setDateTo] = useState(new Date().toISOString().slice(0, 10));
  const [groupBy, setGroupBy] = useState('day');
  const [branchFilter, setBranchFilter] = useState('');
  const [branches, setBranches] = useState([]);

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  useEffect(() => { loadBranches(); }, []);
  useEffect(() => { loadReport(); }, [activeTab, dateFrom, dateTo, groupBy, branchFilter]);

  const loadBranches = async () => {
    try {
      const res = await api('/api/branches');
      if (res.ok) setBranches(await res.json());
    } catch (err) { console.error(err); }
  };

  const loadReport = async () => {
    setLoading(true);
    try {
      let url = '';
      switch (activeTab) {
        case 'sales':
          url = `/api/reports/sales?date_from=${dateFrom}&date_to=${dateTo}&group_by=${groupBy}`;
          if (branchFilter) url += `&branch_id=${branchFilter}`;
          break;
        case 'products':
          url = `/api/reports/product-performance?date_from=${dateFrom}&date_to=${dateTo}&limit=50`;
          if (branchFilter) url += `&branch_id=${branchFilter}`;
          break;
        case 'inventory':
          url = `/api/reports/inventory`;
          if (branchFilter) url += `?branch_id=${branchFilter}`;
          break;
        case 'branch':
          url = `/api/reports/branch-comparison?date_from=${dateFrom}&date_to=${dateTo}`;
          break;
        case 'customers':
          url = `/api/reports/customer-analysis?date_from=${dateFrom}&date_to=${dateTo}`;
          break;
        default:
          return;
      }
      const res = await api(url);
      if (res.ok) setReportData(await res.json());
    } catch (err) { toast.error('Gagal memuat laporan'); }
    finally { setLoading(false); }
  };

  const tabs = [
    { id: 'sales', label: 'Penjualan', icon: TrendingUp },
    { id: 'products', label: 'Produk', icon: Package },
    { id: 'inventory', label: 'Stok', icon: BarChart3 },
    { id: 'branch', label: 'Cabang', icon: Building2 },
    { id: 'customers', label: 'Pelanggan', icon: Users }
  ];

  const groupOptions = [
    { value: 'day', label: 'Harian' },
    { value: 'branch', label: 'Per Cabang' },
    { value: 'product', label: 'Per Produk' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Laporan</h1>
          <p className="text-gray-400">Analisis bisnis dan performa</p>
        </div>
        <div className="flex gap-2 items-center">
          <Calendar className="h-4 w-4 text-gray-400" />
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm" />
          <span className="text-gray-400">-</span>
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm" />
        </div>
      </div>

      <div className="flex flex-wrap gap-2 items-center justify-between border-b border-red-900/30 pb-2">
        <div className="flex gap-2">
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${activeTab === tab.id ? 'bg-red-900/30 text-amber-400' : 'text-gray-400 hover:text-white hover:bg-red-900/20'}`}>
              <tab.icon className="h-4 w-4" /> {tab.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          {activeTab === 'sales' && (
            <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)} className="px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm">
              {groupOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          )}
          {user?.role === 'owner' || user?.role === 'admin' ? (
            <select value={branchFilter} onChange={(e) => setBranchFilter(e.target.value)} className="px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm">
              <option value="">Semua Cabang</option>
              {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          ) : null}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-red-400" /></div>
      ) : (
        <>
          {/* Tab Penjualan */}
          {activeTab === 'sales' && reportData && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Penjualan</div>
                  <div className="text-2xl font-bold text-green-400">{formatRupiah(reportData.totals?.net_sales)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Laba</div>
                  <div className="text-2xl font-bold text-amber-400">{formatRupiah(reportData.totals?.profit)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Transaksi</div>
                  <div className="text-2xl font-bold">{reportData.totals?.transactions || 0}</div>
                </div>
              </div>

              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold">{groupBy === 'day' ? 'Tanggal' : groupBy === 'branch' ? 'Cabang' : 'Produk'}</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Penjualan</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Laba</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Transaksi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.data?.length === 0 ? (
                      <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
                    ) : (
                      reportData.data?.map((item, idx) => (
                        <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                          <td className="px-4 py-3">
                            {groupBy === 'day' ? new Date(item._id).toLocaleDateString('id-ID') :
                             groupBy === 'branch' ? item.branch_name :
                             item.product_name || item._id}
                          </td>
                          <td className="px-4 py-3 text-right text-green-400 font-semibold">{formatRupiah(item.net_sales)}</td>
                          <td className="px-4 py-3 text-right text-amber-400">{formatRupiah(item.profit)}</td>
                          <td className="px-4 py-3 text-right">{item.transactions || '-'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Produk */}
          {activeTab === 'products' && reportData && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Pendapatan</div>
                  <div className="text-2xl font-bold text-green-400">{formatRupiah(reportData.totals?.total_revenue)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Laba</div>
                  <div className="text-2xl font-bold text-amber-400">{formatRupiah(reportData.totals?.total_profit)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Qty Terjual</div>
                  <div className="text-2xl font-bold">{reportData.totals?.total_quantity || 0}</div>
                </div>
              </div>

              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Terjual</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Pendapatan</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Laba</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Margin</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.data?.length === 0 ? (
                      <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
                    ) : (
                      reportData.data?.map((item, idx) => (
                        <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                          <td className="px-4 py-3">
                            <div className="font-medium">{item.product_name}</div>
                            <div className="text-sm text-gray-400">{item.product_code}</div>
                          </td>
                          <td className="px-4 py-3 text-right font-semibold">{item.quantity_sold}</td>
                          <td className="px-4 py-3 text-right text-green-400">{formatRupiah(item.net_revenue)}</td>
                          <td className="px-4 py-3 text-right text-amber-400">{formatRupiah(item.profit)}</td>
                          <td className="px-4 py-3 text-right">{item.profit_margin?.toFixed(1)}%</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Stok */}
          {activeTab === 'inventory' && reportData && (
            <div className="space-y-6">
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Jenis Produk</div>
                  <div className="text-2xl font-bold">{reportData.summary?.total_products || 0}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Item</div>
                  <div className="text-2xl font-bold">{reportData.summary?.total_items || 0}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Nilai Stok (Modal)</div>
                  <div className="text-2xl font-bold text-amber-400">{formatRupiah(reportData.summary?.total_stock_value)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Nilai Jual</div>
                  <div className="text-2xl font-bold text-green-400">{formatRupiah(reportData.summary?.total_retail_value)}</div>
                </div>
              </div>

              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Stok</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Min</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Nilai Modal</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Nilai Jual</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.data?.length === 0 ? (
                      <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
                    ) : (
                      reportData.data?.slice(0, 50).map((item, idx) => (
                        <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                          <td className="px-4 py-3">
                            <div className="font-medium">{item.product_name}</div>
                            <div className="text-sm text-gray-400">{item.product_code}</div>
                          </td>
                          <td className="px-4 py-3 text-right font-semibold">{item.quantity}</td>
                          <td className="px-4 py-3 text-right text-gray-400">{item.min_stock}</td>
                          <td className="px-4 py-3 text-right">{formatRupiah(item.stock_value)}</td>
                          <td className="px-4 py-3 text-right text-green-400">{formatRupiah(item.retail_value)}</td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${item.is_low_stock ? 'bg-red-900/30 text-red-400' : 'bg-green-900/30 text-green-400'}`}>
                              {item.is_low_stock ? 'Menipis' : 'Aman'}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Cabang */}
          {activeTab === 'branch' && reportData && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Penjualan</div>
                  <div className="text-2xl font-bold text-green-400">{formatRupiah(reportData.totals?.total_sales)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Laba</div>
                  <div className="text-2xl font-bold text-amber-400">{formatRupiah(reportData.totals?.total_profit)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Transaksi</div>
                  <div className="text-2xl font-bold">{reportData.totals?.total_transactions || 0}</div>
                </div>
              </div>

              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Cabang</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Penjualan</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Laba</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Margin</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Transaksi</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Rata-rata</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.branches?.length === 0 ? (
                      <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
                    ) : (
                      reportData.branches?.map((item, idx) => (
                        <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                          <td className="px-4 py-3">
                            <div className="font-medium">{item.branch_name}</div>
                            <div className="text-sm text-gray-400">{item.branch_code}</div>
                          </td>
                          <td className="px-4 py-3 text-right text-green-400 font-semibold">{formatRupiah(item.total_sales)}</td>
                          <td className="px-4 py-3 text-right text-amber-400">{formatRupiah(item.total_profit)}</td>
                          <td className="px-4 py-3 text-right">{item.profit_margin?.toFixed(1)}%</td>
                          <td className="px-4 py-3 text-right">{item.transactions}</td>
                          <td className="px-4 py-3 text-right text-gray-400">{formatRupiah(item.avg_transaction)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Pelanggan */}
          {activeTab === 'customers' && reportData && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Pelanggan</div>
                  <div className="text-2xl font-bold">{reportData.total_customers || 0}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Pelanggan Baru</div>
                  <div className="text-2xl font-bold text-green-400">{reportData.new_customers || 0}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
                  <h3 className="text-lg font-semibold mb-4 text-amber-100">Segmen Pelanggan</h3>
                  <div className="space-y-3">
                    {reportData.segments?.map((seg, idx) => (
                      <div key={idx} className="flex justify-between items-center">
                        <span className="capitalize">{seg._id || 'Unknown'}</span>
                        <div className="text-right">
                          <div className="font-semibold">{seg.count}</div>
                          <div className="text-sm text-gray-400">{formatRupiah(seg.total_spent)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
                  <h3 className="text-lg font-semibold mb-4 text-amber-100">Top Pelanggan</h3>
                  <div className="space-y-3">
                    {reportData.top_customers?.slice(0, 5).map((cust, idx) => (
                      <div key={idx} className="flex justify-between items-center">
                        <div>
                          <div className="font-medium">{cust.customer_name}</div>
                          <div className="text-sm text-gray-400">{cust.transactions} transaksi</div>
                        </div>
                        <div className="text-amber-400 font-semibold">{formatRupiah(cust.total_spent)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Reports;
