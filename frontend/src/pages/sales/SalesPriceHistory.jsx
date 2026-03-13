import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Search, Loader2, RefreshCw, History, Download, Printer } from 'lucide-react';
import { toast } from 'sonner';

/**
 * SalesPriceHistory - Halaman Read-Only untuk History Harga Jual
 * Modul ini adalah READ-ONLY karena hanya menampilkan histori
 * Toolbar: Export, Print, Refresh
 */
const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

const SalesPriceHistory = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [filters, setFilters] = useState({
    product_from: '', product_to: '', date_from: '', date_to: '', customer_id: ''
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.customer_id) params.append('customer_id', filters.customer_id);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      
      const [histRes, custRes] = await Promise.all([
        api(`/api/sales/price-history?${params}`),
        api('/api/customers')
      ]);
      
      if (histRes.ok) setHistory((await histRes.json()).items || []);
      if (custRes.ok) setCustomers((await custRes.json()).items || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [api, filters]);

  useEffect(() => { loadData(); }, []);

  const handleExport = () => { toast.info('Export ke Excel akan segera tersedia'); };
  const handlePrint = () => { toast.info('Mencetak history harga...'); window.print(); };
  const handleRowSelect = (item) => { setSelectedItem(selectedItem?.id === item.id ? null : item); };

  return (
    <div className="space-y-4 p-4" data-testid="sales-price-history-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2"><History className="h-6 w-6" /> History Harga Jual</h1>
          <p className="text-gray-400 text-sm">Riwayat harga jual per pelanggan (Read-Only)</p>
        </div>
      </div>

      <div className="bg-[#1a1214] rounded-lg border border-red-900/30 p-3">
        <div className="grid grid-cols-6 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Dari Item</label>
            <input type="text" value={filters.product_from} onChange={e => setFilters(p => ({...p, product_from: e.target.value}))} className="w-full px-3 py-1.5 bg-[#0a0608] border border-red-900/30 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sampai Item</label>
            <input type="text" value={filters.product_to} onChange={e => setFilters(p => ({...p, product_to: e.target.value}))} className="w-full px-3 py-1.5 bg-[#0a0608] border border-red-900/30 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Dari Tanggal</label>
            <input type="date" value={filters.date_from} onChange={e => setFilters(p => ({...p, date_from: e.target.value}))} className="w-full px-3 py-1.5 bg-[#0a0608] border border-red-900/30 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sampai Tanggal</label>
            <input type="date" value={filters.date_to} onChange={e => setFilters(p => ({...p, date_to: e.target.value}))} className="w-full px-3 py-1.5 bg-[#0a0608] border border-red-900/30 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Pelanggan</label>
            <select value={filters.customer_id} onChange={e => setFilters(p => ({...p, customer_id: e.target.value}))} className="w-full px-3 py-1.5 bg-[#0a0608] border border-red-900/30 rounded text-sm text-white">
              <option value="">Semua</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={loadData} className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2 text-sm"><Search className="h-4 w-4" /> Proses</button>
          </div>
        </div>
      </div>

      {/* TOOLBAR UNTUK MODUL READ-ONLY */}
      <div className="flex items-center gap-2 p-3 bg-[#1a1214] border border-red-900/30 rounded-lg">
        <span className="text-xs text-gray-500 mr-2">Read-Only Module:</span>
        <button onClick={handleExport} className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-emerald-600 hover:bg-emerald-700 text-white">
          <Download className="h-4 w-4" /> Export
        </button>
        <button onClick={handlePrint} className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white">
          <Printer className="h-4 w-4" /> Print
        </button>
        <button onClick={loadData} className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-gray-600 hover:bg-gray-700 text-white">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
        <div className="flex-1" />
        {selectedItem && (
          <div className="text-xs text-amber-400 bg-amber-900/20 px-2 py-1 rounded">
            Dipilih: <span className="font-medium text-amber-300">{selectedItem.product_name}</span>
          </div>
        )}
      </div>

      <div className="bg-[#1a1214] rounded-lg border border-red-900/30 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-red-900/20">
              <tr className="text-left text-amber-200 text-xs">
                <th className="p-2 border-b border-red-900/30 w-10"><input type="checkbox" className="w-3 h-3" disabled /></th>
                <th className="p-2 border-b border-red-900/30">Pelanggan</th>
                <th className="p-2 border-b border-red-900/30">No Transaksi</th>
                <th className="p-2 border-b border-red-900/30">Tanggal</th>
                <th className="p-2 border-b border-red-900/30">Kode Item</th>
                <th className="p-2 border-b border-red-900/30">Nama Item</th>
                <th className="p-2 border-b border-red-900/30">Satuan</th>
                <th className="p-2 border-b border-red-900/30 text-right">Harga</th>
                <th className="p-2 border-b border-red-900/30 text-right">Jumlah</th>
                <th className="p-2 border-b border-red-900/30 text-right">Potongan</th>
                <th className="p-2 border-b border-red-900/30">Sales</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan="11" className="p-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></td></tr>
              ) : history.length === 0 ? (
                <tr><td colSpan="11" className="p-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : history.map((h, idx) => (
                <tr key={idx} onClick={() => handleRowSelect(h)}
                  className={`cursor-pointer transition-colors ${selectedItem?.id === h.id ? 'bg-amber-900/30 border-l-2 border-amber-500' : 'hover:bg-red-900/10'}`}
                  data-testid={`history-row-${idx}`}>
                  <td className="p-2 text-center"><input type="radio" checked={selectedItem?.id === h.id} onChange={() => handleRowSelect(h)} className="w-3 h-3 accent-amber-500" /></td>
                  <td className="p-2">{h.customer_name}</td>
                  <td className="p-2 text-blue-400">{h.invoice_number}</td>
                  <td className="p-2">{formatDate(h.date)}</td>
                  <td className="p-2 font-mono">{h.product_code}</td>
                  <td className="p-2">{h.product_name}</td>
                  <td className="p-2">{h.unit}</td>
                  <td className="p-2 text-right">{formatRupiah(h.unit_price)}</td>
                  <td className="p-2 text-right">{h.quantity}</td>
                  <td className="p-2 text-right">{h.discount_percent}%</td>
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
