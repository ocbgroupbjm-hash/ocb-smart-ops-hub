import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Plus, Search, Eye, Printer, Trash2, Loader2, RefreshCw, RotateCcw
} from 'lucide-react';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

const SalesReturnList = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [returns, setReturns] = useState([]);
  const [filters, setFilters] = useState({ keyword: '', dateFrom: '', dateTo: '' });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api('/api/sales/returns');
      if (res.ok) setReturns((await res.json()).items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredReturns = useMemo(() => {
    return returns.filter(r => {
      if (filters.keyword) {
        const kw = filters.keyword.toLowerCase();
        if (!r.return_number?.toLowerCase().includes(kw) && 
            !r.customer_name?.toLowerCase().includes(kw)) return false;
      }
      return true;
    });
  }, [returns, filters]);

  const summary = useMemo(() => {
    return filteredReturns.reduce((acc, r) => ({
      count: acc.count + 1,
      total: acc.total + (r.total || 0),
    }), { count: 0, total: 0 });
  }, [filteredReturns]);

  return (
    <div className="space-y-4 p-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <RotateCcw className="h-5 w-5 text-blue-400" />
          Daftar Retur Penjualan
        </h2>
        <a href="/sales/returns/add" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2 text-sm">
          <Plus className="h-4 w-4" /> Tambah
        </a>
      </div>

      {/* Filters */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="grid grid-cols-4 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Kata Kunci</label>
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />
              <input type="text" value={filters.keyword} onChange={e => setFilters(p => ({...p, keyword: e.target.value}))} placeholder="Cari..." className="w-full pl-8 pr-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Dari Tanggal</label>
            <input type="date" value={filters.dateFrom} onChange={e => setFilters(p => ({...p, dateFrom: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sampai Tanggal</label>
            <input type="date" value={filters.dateTo} onChange={e => setFilters(p => ({...p, dateTo: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
          </div>
          <div className="flex items-end">
            <button onClick={loadData} className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2 text-sm">
              <RefreshCw className="h-4 w-4" /> Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-800">
              <tr className="text-left text-gray-400 text-xs">
                <th className="p-2 border-b border-gray-700">No Transaksi</th>
                <th className="p-2 border-b border-gray-700">Tanggal</th>
                <th className="p-2 border-b border-gray-700">Kd Pelanggan</th>
                <th className="p-2 border-b border-gray-700">Nama</th>
                <th className="p-2 border-b border-gray-700">Keterangan</th>
                <th className="p-2 border-b border-gray-700 text-right">Total</th>
                <th className="p-2 border-b border-gray-700">PPN</th>
                <th className="p-2 border-b border-gray-700">User</th>
                <th className="p-2 border-b border-gray-700">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {loading ? (
                <tr><td colSpan="9" className="p-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></td></tr>
              ) : filteredReturns.length === 0 ? (
                <tr><td colSpan="9" className="p-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : filteredReturns.map(r => (
                <tr key={r.id} className="hover:bg-gray-800/30">
                  <td className="p-2 text-blue-400 font-medium">{r.return_number}</td>
                  <td className="p-2">{formatDate(r.created_at)}</td>
                  <td className="p-2 font-mono text-xs">{r.customer_code || '-'}</td>
                  <td className="p-2">{r.customer_name}</td>
                  <td className="p-2 text-xs">{r.notes || '-'}</td>
                  <td className="p-2 text-right font-medium text-red-400">{formatRupiah(r.total)}</td>
                  <td className="p-2">{r.ppn_type || '-'}</td>
                  <td className="p-2 text-xs">{r.user_name || '-'}</td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      <button className="p-1 hover:bg-gray-700 rounded"><Eye className="h-3.5 w-3.5" /></button>
                      <button className="p-1 hover:bg-gray-700 rounded"><Printer className="h-3.5 w-3.5" /></button>
                      <button className="p-1 hover:bg-red-700 rounded"><Trash2 className="h-3.5 w-3.5 text-red-400" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="grid grid-cols-2 gap-4 text-sm text-center">
          <div>
            <p className="text-gray-400 text-xs">Jumlah Retur</p>
            <p className="font-bold text-lg">{summary.count}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs">Total Retur</p>
            <p className="font-bold text-lg text-red-400">{formatRupiah(summary.total)}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SalesReturnList;
