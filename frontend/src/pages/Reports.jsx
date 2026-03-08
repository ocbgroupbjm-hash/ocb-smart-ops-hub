import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { BarChart3, TrendingUp, Package, Users, Building2, Loader2, Download, Calendar, FileText, Printer, FileSpreadsheet } from 'lucide-react';
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
  const [exporting, setExporting] = useState(false);

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
        case 'best-sellers':
          url = `/api/reports/best-sellers?date_from=${dateFrom}&date_to=${dateTo}&limit=20`;
          if (branchFilter) url += `&branch_id=${branchFilter}`;
          break;
        case 'cashiers':
          url = `/api/reports/cashiers?date_from=${dateFrom}&date_to=${dateTo}`;
          if (branchFilter) url += `&branch_id=${branchFilter}`;
          break;
        case 'payables':
          url = `/api/reports/payables`;
          break;
        case 'receivables':
          url = `/api/reports/receivables`;
          break;
        default:
          return;
      }
      const res = await api(url);
      if (res.ok) setReportData(await res.json());
    } catch (err) { toast.error('Gagal memuat laporan'); }
    finally { setLoading(false); }
  };

  const handleExport = async (type) => {
    setExporting(true);
    try {
      const token = localStorage.getItem('token');
      const url = `${process.env.REACT_APP_BACKEND_URL}/api/reports/export/excel/${activeTab}?date_from=${dateFrom}&date_to=${dateTo}&branch_id=${branchFilter}`;
      
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        const blob = await res.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `laporan_${activeTab}_${dateFrom}_${dateTo}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);
        toast.success('Export berhasil!');
      } else {
        toast.error('Gagal export laporan');
      }
    } catch (err) {
      toast.error('Gagal export laporan');
    }
    finally { setExporting(false); }
  };

  const tabs = [
    { id: 'sales', label: 'Penjualan', icon: TrendingUp },
    { id: 'products', label: 'Produk', icon: Package },
    { id: 'best-sellers', label: 'Terlaris', icon: BarChart3 },
    { id: 'inventory', label: 'Stok', icon: BarChart3 },
    { id: 'branch', label: 'Cabang', icon: Building2 },
    { id: 'cashiers', label: 'Kasir', icon: Users },
    { id: 'customers', label: 'Pelanggan', icon: Users },
    { id: 'payables', label: 'Hutang', icon: FileText },
    { id: 'receivables', label: 'Piutang', icon: FileText }
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
          <button 
            onClick={() => handleExport('excel')} 
            disabled={exporting}
            className="px-3 py-2 bg-green-600/20 text-green-400 rounded-lg flex items-center gap-2 hover:bg-green-600/30 disabled:opacity-50"
          >
            <FileSpreadsheet className="h-4 w-4" />
            {exporting ? 'Exporting...' : 'Export Excel'}
          </button>
          <div className="flex gap-2 items-center ml-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm" />
            <span className="text-gray-400">-</span>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm" />
          </div>
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

          {/* Tab Best Sellers */}
          {activeTab === 'best-sellers' && reportData && (
            <div className="space-y-6">
              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                <div className="text-gray-400 mb-1">Total Produk Terlaris</div>
                <div className="text-2xl font-bold text-amber-400">{reportData.total_items || reportData.items?.length || 0}</div>
              </div>

              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold">No</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Qty Terjual</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Pendapatan</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Laba</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.items?.length === 0 ? (
                      <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
                    ) : (
                      reportData.items?.map((item, idx) => (
                        <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                          <td className="px-4 py-3 text-amber-400 font-bold">{idx + 1}</td>
                          <td className="px-4 py-3">
                            <div className="font-medium">{item.product_name}</div>
                            <div className="text-sm text-gray-400">{item.product_code}</div>
                          </td>
                          <td className="px-4 py-3 text-right font-semibold">{item.quantity_sold}</td>
                          <td className="px-4 py-3 text-right text-green-400">{formatRupiah(item.revenue)}</td>
                          <td className="px-4 py-3 text-right text-amber-400">{formatRupiah(item.profit)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Kasir */}
          {activeTab === 'cashiers' && reportData && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Kasir</div>
                  <div className="text-2xl font-bold">{reportData.total_cashiers || 0}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Penjualan</div>
                  <div className="text-2xl font-bold text-green-400">{formatRupiah(reportData.total_sales)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Rata-rata per Kasir</div>
                  <div className="text-2xl font-bold text-amber-400">
                    {formatRupiah(reportData.total_cashiers ? reportData.total_sales / reportData.total_cashiers : 0)}
                  </div>
                </div>
              </div>

              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Kasir</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Total Penjualan</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Transaksi</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Rata-rata</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Laba</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.items?.length === 0 ? (
                      <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
                    ) : (
                      reportData.items?.map((item, idx) => (
                        <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                          <td className="px-4 py-3 font-medium">{item.cashier_name}</td>
                          <td className="px-4 py-3 text-right text-green-400 font-semibold">{formatRupiah(item.total_sales)}</td>
                          <td className="px-4 py-3 text-right">{item.total_transactions}</td>
                          <td className="px-4 py-3 text-right text-gray-400">{formatRupiah(item.avg_transaction)}</td>
                          <td className="px-4 py-3 text-right text-amber-400">{formatRupiah(item.total_profit)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab Hutang (Payables) */}
          {activeTab === 'payables' && reportData && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Pembelian</div>
                  <div className="text-2xl font-bold">{formatRupiah(reportData.total_purchase)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Sudah Dibayar</div>
                  <div className="text-2xl font-bold text-green-400">{formatRupiah(reportData.total_paid)}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Sisa Hutang</div>
                  <div className="text-2xl font-bold text-red-400">{formatRupiah(reportData.total_payable)}</div>
                </div>
              </div>

              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold">No. PO</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Supplier</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Total</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Dibayar</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Sisa</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.items?.length === 0 ? (
                      <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Tidak ada hutang</td></tr>
                    ) : (
                      reportData.items?.map((item, idx) => (
                        <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                          <td className="px-4 py-3 font-mono text-amber-300">{item.po_number}</td>
                          <td className="px-4 py-3">{item.supplier_name}</td>
                          <td className="px-4 py-3 text-right">{formatRupiah(item.total)}</td>
                          <td className="px-4 py-3 text-right text-green-400">{formatRupiah(item.paid_amount)}</td>
                          <td className="px-4 py-3 text-right text-red-400">{formatRupiah(Math.max(0, item.total - item.paid_amount))}</td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${
                              item.paid_amount >= item.total ? 'bg-green-600/20 text-green-400' : 
                              item.paid_amount > 0 ? 'bg-yellow-600/20 text-yellow-400' : 'bg-red-600/20 text-red-400'
                            }`}>
                              {item.paid_amount >= item.total ? 'Lunas' : item.paid_amount > 0 ? 'Sebagian' : 'Belum Bayar'}
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

          {/* Tab Piutang (Receivables) */}
          {activeTab === 'receivables' && reportData && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Pelanggan dengan Piutang</div>
                  <div className="text-2xl font-bold">{reportData.customer_count || 0}</div>
                </div>
                <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
                  <div className="text-gray-400 mb-1">Total Piutang</div>
                  <div className="text-2xl font-bold text-amber-400">{formatRupiah(reportData.total_receivable)}</div>
                </div>
              </div>

              <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Pelanggan</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Telepon</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold">Segmen</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Piutang</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Limit Kredit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.items?.length === 0 ? (
                      <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Tidak ada piutang</td></tr>
                    ) : (
                      reportData.items?.map((item, idx) => (
                        <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                          <td className="px-4 py-3">
                            <div className="font-medium">{item.name}</div>
                            <div className="text-sm text-gray-400">{item.code}</div>
                          </td>
                          <td className="px-4 py-3 text-gray-400">{item.phone}</td>
                          <td className="px-4 py-3 text-center">
                            <span className="px-2 py-1 rounded text-xs bg-blue-600/20 text-blue-400 capitalize">{item.segment}</span>
                          </td>
                          <td className="px-4 py-3 text-right text-amber-400 font-semibold">{formatRupiah(item.credit_balance)}</td>
                          <td className="px-4 py-3 text-right text-gray-400">{formatRupiah(item.credit_limit)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Reports;
