import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Search, Eye, Printer, Loader2, RefreshCw, Send, Edit
} from 'lucide-react';

const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

const DeliveriesList = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [deliveries, setDeliveries] = useState([]);
  const [filters, setFilters] = useState({ keyword: '', tracking_no: '', courier: '', status: '' });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api('/api/sales/deliveries');
      if (res.ok) setDeliveries((await res.json()).items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredDeliveries = useMemo(() => {
    return deliveries.filter(d => {
      if (filters.keyword) {
        const kw = filters.keyword.toLowerCase();
        if (!d.transaction_number?.toLowerCase().includes(kw) && 
            !d.customer_name?.toLowerCase().includes(kw)) return false;
      }
      if (filters.status && d.status !== filters.status) return false;
      return true;
    });
  }, [deliveries, filters]);

  const getStatusColor = (status) => {
    switch(status) {
      case 'pending': return 'bg-yellow-600/20 text-yellow-300';
      case 'processing': return 'bg-blue-600/20 text-blue-300';
      case 'shipped': return 'bg-purple-600/20 text-purple-300';
      case 'delivered': return 'bg-green-600/20 text-green-300';
      case 'cancelled': return 'bg-red-600/20 text-red-300';
      default: return 'bg-gray-600/20 text-gray-300';
    }
  };

  const getStatusLabel = (status) => {
    switch(status) {
      case 'pending': return 'Belum Kirim';
      case 'processing': return 'Proses';
      case 'shipped': return 'Dikirim';
      case 'delivered': return 'Terkirim';
      case 'cancelled': return 'Batal';
      default: return status;
    }
  };

  return (
    <div className="space-y-4 p-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <Send className="h-5 w-5 text-blue-400" />
          Daftar Pengiriman
        </h2>
      </div>

      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="grid grid-cols-5 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Kata Kunci</label>
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />
              <input type="text" value={filters.keyword} onChange={e => setFilters(p => ({...p, keyword: e.target.value}))} placeholder="Cari..." className="w-full pl-8 pr-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">No Resi</label>
            <input type="text" value={filters.tracking_no} onChange={e => setFilters(p => ({...p, tracking_no: e.target.value}))} placeholder="Resi..." className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Kurir</label>
            <select value={filters.courier} onChange={e => setFilters(p => ({...p, courier: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white">
              <option value="">Semua Kurir</option>
              <option value="jne">JNE</option>
              <option value="jnt">J&T</option>
              <option value="sicepat">SiCepat</option>
              <option value="anteraja">AnterAja</option>
              <option value="internal">Internal</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Status Kirim</label>
            <select value={filters.status} onChange={e => setFilters(p => ({...p, status: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white">
              <option value="">Semua Status</option>
              <option value="pending">Belum Kirim</option>
              <option value="processing">Proses</option>
              <option value="shipped">Dikirim</option>
              <option value="delivered">Terkirim</option>
              <option value="cancelled">Batal</option>
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={loadData} className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2 text-sm">
              <RefreshCw className="h-4 w-4" /> Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-800">
              <tr className="text-left text-gray-400 text-xs">
                <th className="p-2 border-b border-gray-700">No Transaksi</th>
                <th className="p-2 border-b border-gray-700">Dari</th>
                <th className="p-2 border-b border-gray-700">Kepada</th>
                <th className="p-2 border-b border-gray-700 text-right">Total Pesan</th>
                <th className="p-2 border-b border-gray-700">Status</th>
                <th className="p-2 border-b border-gray-700">Tgl Kirim</th>
                <th className="p-2 border-b border-gray-700">Kurir</th>
                <th className="p-2 border-b border-gray-700">No Resi</th>
                <th className="p-2 border-b border-gray-700">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {loading ? (
                <tr><td colSpan="9" className="p-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></td></tr>
              ) : filteredDeliveries.length === 0 ? (
                <tr><td colSpan="9" className="p-8 text-center text-gray-400">Tidak ada data pengiriman</td></tr>
              ) : filteredDeliveries.map(d => (
                <tr key={d.id} className="hover:bg-gray-800/30">
                  <td className="p-2 text-blue-400 font-medium">{d.transaction_number}</td>
                  <td className="p-2">{d.from_warehouse || d.from_branch || '-'}</td>
                  <td className="p-2">{d.customer_name}</td>
                  <td className="p-2 text-right">{d.total_items || 0}</td>
                  <td className="p-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(d.status)}`}>
                      {getStatusLabel(d.status)}
                    </span>
                  </td>
                  <td className="p-2">{formatDate(d.ship_date)}</td>
                  <td className="p-2">{d.courier?.toUpperCase() || '-'}</td>
                  <td className="p-2 font-mono text-xs">{d.tracking_number || '-'}</td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      <button className="p-1 hover:bg-gray-700 rounded" title="Edit"><Edit className="h-3.5 w-3.5" /></button>
                      <button className="p-1 hover:bg-gray-700 rounded" title="Cetak"><Printer className="h-3.5 w-3.5" /></button>
                      <button className="p-1 hover:bg-blue-700 rounded" title="Lacak">
                        <Eye className="h-3.5 w-3.5 text-blue-400" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DeliveriesList;
