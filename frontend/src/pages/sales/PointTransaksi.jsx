import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Search, Loader2, RefreshCw, Star
} from 'lucide-react';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

const PointTransaksi = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [points, setPoints] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [filters, setFilters] = useState({ customer_id: '', dateFrom: '', dateTo: '' });
  const [selectedCustomer, setSelectedCustomer] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [pointsRes, custRes] = await Promise.all([
        api(`/api/sales/points${filters.customer_id ? `?customer_id=${filters.customer_id}` : ''}`),
        api('/api/customers')
      ]);
      
      if (pointsRes.ok) setPoints((await pointsRes.json()).items || []);
      if (custRes.ok) setCustomers((await custRes.json()).items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [api, filters.customer_id]);

  useEffect(() => { loadData(); }, [loadData]);

  const totalPoints = useMemo(() => {
    return points.reduce((acc, p) => acc + (p.points || 0), 0);
  }, [points]);

  const handleCustomerChange = (customerId) => {
    setFilters(p => ({...p, customer_id: customerId}));
    const cust = customers.find(c => c.id === customerId);
    setSelectedCustomer(cust);
  };

  return (
    <div className="space-y-4 p-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <Star className="h-5 w-5 text-yellow-400" />
          Point Transaksi
        </h2>
      </div>

      {/* Filters */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="grid grid-cols-4 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Pelanggan</label>
            <select value={filters.customer_id} onChange={e => handleCustomerChange(e.target.value)} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white">
              <option value="">Pilih Pelanggan</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.code} - {c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Periode Point Dari</label>
            <input type="date" value={filters.dateFrom} onChange={e => setFilters(p => ({...p, dateFrom: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sampai</label>
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
                <th className="p-2 border-b border-gray-700">Tipe Transaksi</th>
                <th className="p-2 border-b border-gray-700">Tanggal</th>
                <th className="p-2 border-b border-gray-700 text-right">Total Transaksi</th>
                <th className="p-2 border-b border-gray-700 text-right">Point</th>
                <th className="p-2 border-b border-gray-700">Keterangan</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {loading ? (
                <tr><td colSpan="6" className="p-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></td></tr>
              ) : points.length === 0 ? (
                <tr><td colSpan="6" className="p-8 text-center text-gray-400">Pilih pelanggan untuk melihat point</td></tr>
              ) : points.map((p, idx) => (
                <tr key={idx} className="hover:bg-gray-800/30">
                  <td className="p-2 text-blue-400">{p.transaction_number}</td>
                  <td className="p-2">{p.transaction_type || 'Penjualan'}</td>
                  <td className="p-2">{formatDate(p.date)}</td>
                  <td className="p-2 text-right">{formatRupiah(p.transaction_total)}</td>
                  <td className="p-2 text-right font-medium text-yellow-400">+{p.points}</td>
                  <td className="p-2 text-xs">{p.notes || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Point Summary */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-gray-400 text-sm">Sisa Point</p>
            <p className="text-3xl font-bold text-yellow-400">{totalPoints.toLocaleString()}</p>
          </div>
          <div className="flex gap-2">
            <button className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-sm font-medium">
              Ambil Point
            </button>
            <button className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-sm font-medium">
              Hapus Ambil Point
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PointTransaksi;
