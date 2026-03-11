import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Search, Loader2, RefreshCw, History
} from 'lucide-react';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

const SalesPriceHistory = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [salesPersons, setSalesPersons] = useState([]);
  const [filters, setFilters] = useState({
    product_from: '', product_to: '',
    date_from: '', date_to: '',
    customer_id: '', sales_id: ''
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.customer_id) params.append('customer_id', filters.customer_id);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      
      const [histRes, custRes, salesRes] = await Promise.all([
        api(`/api/sales/price-history?${params}`),
        api('/api/customers'),
        api('/api/sales-persons')
      ]);
      
      if (histRes.ok) setHistory((await histRes.json()).items || []);
      if (custRes.ok) setCustomers((await custRes.json()).items || []);
      if (salesRes.ok) setSalesPersons((await salesRes.json()) || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [api, filters]);

  useEffect(() => { loadData(); }, []);

  return (
    <div className="space-y-4 p-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <History className="h-5 w-5 text-blue-400" />
          History Harga Jual
        </h2>
      </div>

      {/* Filters */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="grid grid-cols-6 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Dari Item</label>
            <input type="text" value={filters.product_from} onChange={e => setFilters(p => ({...p, product_from: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sampai Item</label>
            <input type="text" value={filters.product_to} onChange={e => setFilters(p => ({...p, product_to: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Dari Tanggal</label>
            <input type="date" value={filters.date_from} onChange={e => setFilters(p => ({...p, date_from: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sampai Tanggal</label>
            <input type="date" value={filters.date_to} onChange={e => setFilters(p => ({...p, date_to: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Pelanggan</label>
            <select value={filters.customer_id} onChange={e => setFilters(p => ({...p, customer_id: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white">
              <option value="">Semua</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={loadData} className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2 text-sm">
              <Search className="h-4 w-4" /> Proses
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
                <th className="p-2 border-b border-gray-700">Pelanggan</th>
                <th className="p-2 border-b border-gray-700">No Transaksi</th>
                <th className="p-2 border-b border-gray-700">Tanggal</th>
                <th className="p-2 border-b border-gray-700">Kode Item</th>
                <th className="p-2 border-b border-gray-700">Nama Item</th>
                <th className="p-2 border-b border-gray-700">Satuan</th>
                <th className="p-2 border-b border-gray-700 text-right">Harga</th>
                <th className="p-2 border-b border-gray-700 text-right">Jumlah</th>
                <th className="p-2 border-b border-gray-700 text-right">Potongan</th>
                <th className="p-2 border-b border-gray-700 text-right">Tax</th>
                <th className="p-2 border-b border-gray-700">Sales</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {loading ? (
                <tr><td colSpan="11" className="p-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></td></tr>
              ) : history.length === 0 ? (
                <tr><td colSpan="11" className="p-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : history.map((h, idx) => (
                <tr key={idx} className="hover:bg-gray-800/30">
                  <td className="p-2">{h.customer_name}</td>
                  <td className="p-2 text-blue-400">{h.invoice_number}</td>
                  <td className="p-2">{formatDate(h.date)}</td>
                  <td className="p-2 font-mono">{h.product_code}</td>
                  <td className="p-2">{h.product_name}</td>
                  <td className="p-2">{h.unit}</td>
                  <td className="p-2 text-right">{formatRupiah(h.unit_price)}</td>
                  <td className="p-2 text-right">{h.quantity}</td>
                  <td className="p-2 text-right">{h.discount_percent}%</td>
                  <td className="p-2 text-right">{h.tax_percent}%</td>
                  <td className="p-2">{h.sales_person_name || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SalesPriceHistory;
