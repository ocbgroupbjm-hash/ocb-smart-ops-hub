import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Plus, Search, Eye, Printer, Edit, Trash2, Save, X, Loader2, FileText, 
  Package, Truck, CreditCard, RotateCcw, History, Calendar, Check, 
  ChevronDown, RefreshCw, Filter, Building2, AlertTriangle, Hash, 
  Barcode, Tag, User, Clock, FileCheck, Percent, DollarSign, Warehouse,
  StickyNote, ArrowUpDown, Download, ShoppingCart, Star, Send
} from 'lucide-react';
import { toast } from 'sonner';

// ==================== UTILITY FUNCTIONS ====================
const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatNumber = (num) => (num || 0).toLocaleString('id-ID');
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';
const formatTime = (date) => date ? new Date(date).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) : '-';

// ==================== STATUS BADGE ====================
const StatusBadge = ({ status }) => {
  const styles = {
    draft: 'bg-gray-600/20 text-gray-300 border-gray-500/30',
    pending: 'bg-yellow-600/20 text-yellow-300 border-yellow-500/30',
    confirmed: 'bg-blue-600/20 text-blue-300 border-blue-500/30',
    shipped: 'bg-purple-600/20 text-purple-300 border-purple-500/30',
    delivered: 'bg-green-600/20 text-green-300 border-green-500/30',
    completed: 'bg-green-600/20 text-green-300 border-green-500/30',
    cancelled: 'bg-red-600/20 text-red-300 border-red-500/30',
    lunas: 'bg-green-600/20 text-green-300 border-green-500/30',
    partial: 'bg-amber-600/20 text-amber-300 border-amber-500/30',
    unpaid: 'bg-red-600/20 text-red-300 border-red-500/30',
  };
  const labels = {
    draft: 'Draft', pending: 'Pending', confirmed: 'Confirmed', 
    shipped: 'Dikirim', delivered: 'Terkirim', completed: 'Selesai',
    cancelled: 'Batal', lunas: 'Lunas', partial: 'Sebagian', unpaid: 'Belum Bayar'
  };
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-medium ${styles[status] || styles.draft}`}>
      {labels[status] || status?.toUpperCase() || 'N/A'}
    </span>
  );
};

// ==================== INPUT FIELD ====================
const InputField = ({ label, value, onChange, type = 'text', placeholder, required, disabled, className = '', options, icon: Icon }) => (
  <div className={className}>
    {label && (
      <label className="block text-xs text-gray-400 mb-1">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
    )}
    <div className="relative">
      {Icon && <Icon className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />}
      {type === 'select' ? (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={`w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white disabled:opacity-50 ${Icon ? 'pl-8' : ''}`}
        >
          <option value="">{placeholder || `Pilih ${label}`}</option>
          {options?.map((opt, idx) => (
            <option key={opt.value || idx} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      ) : (
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={`w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white disabled:opacity-50 ${Icon ? 'pl-8' : ''}`}
        />
      )}
    </div>
  </div>
);

// ==================== SALES ORDER LIST ====================
const SalesOrderList = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [filters, setFilters] = useState({ keyword: '', dateFrom: '', dateTo: '', warehouse_id: '' });
  const [warehouses, setWarehouses] = useState([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [ordersRes, whRes] = await Promise.all([
        api('/api/sales/orders'),
        api('/api/master/warehouses')
      ]);
      if (ordersRes.ok) setOrders((await ordersRes.json()).items || []);
      if (whRes.ok) setWarehouses(await whRes.json() || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredOrders = useMemo(() => {
    return orders.filter(o => {
      if (filters.keyword) {
        const kw = filters.keyword.toLowerCase();
        if (!o.order_number?.toLowerCase().includes(kw) && 
            !o.customer_name?.toLowerCase().includes(kw)) return false;
      }
      return true;
    });
  }, [orders, filters]);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">Pesanan Jual List</h2>
        <a href="/sales/orders/add" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2 text-sm">
          <Plus className="h-4 w-4" /> Tambah
        </a>
      </div>

      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="grid grid-cols-5 gap-3">
          <InputField label="Kata Kunci" value={filters.keyword} onChange={v => setFilters(p => ({...p, keyword: v}))} icon={Search} placeholder="Cari..." />
          <InputField label="Dept / Gudang" type="select" value={filters.warehouse_id} onChange={v => setFilters(p => ({...p, warehouse_id: v}))} options={warehouses.map(w => ({value: w.id, label: w.name}))} />
          <InputField label="Dari Tanggal" type="date" value={filters.dateFrom} onChange={v => setFilters(p => ({...p, dateFrom: v}))} />
          <InputField label="Sampai Tanggal" type="date" value={filters.dateTo} onChange={v => setFilters(p => ({...p, dateTo: v}))} />
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
                <th className="p-2 border-b border-gray-700">Tanggal</th>
                <th className="p-2 border-b border-gray-700">Tgl Kirim</th>
                <th className="p-2 border-b border-gray-700">Kode Pelanggan</th>
                <th className="p-2 border-b border-gray-700">Nama</th>
                <th className="p-2 border-b border-gray-700 text-right">Jml Pesanan</th>
                <th className="p-2 border-b border-gray-700 text-right">Jml Terkirim</th>
                <th className="p-2 border-b border-gray-700">Keterangan</th>
                <th className="p-2 border-b border-gray-700 text-right">Total</th>
                <th className="p-2 border-b border-gray-700">Status</th>
                <th className="p-2 border-b border-gray-700">User</th>
                <th className="p-2 border-b border-gray-700">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {loading ? (
                <tr><td colSpan="12" className="p-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></td></tr>
              ) : filteredOrders.length === 0 ? (
                <tr><td colSpan="12" className="p-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : filteredOrders.map(o => (
                <tr key={o.id} className="hover:bg-gray-800/30">
                  <td className="p-2 text-blue-400 font-medium">{o.order_number}</td>
                  <td className="p-2">{formatDate(o.created_at)}</td>
                  <td className="p-2">{formatDate(o.delivery_date)}</td>
                  <td className="p-2 font-mono text-xs">{o.customer_code || '-'}</td>
                  <td className="p-2">{o.customer_name}</td>
                  <td className="p-2 text-right">{o.total_qty || 0}</td>
                  <td className="p-2 text-right text-green-400">{o.delivered_qty || 0}</td>
                  <td className="p-2 text-xs">{o.notes || '-'}</td>
                  <td className="p-2 text-right font-medium">{formatRupiah(o.total)}</td>
                  <td className="p-2"><StatusBadge status={o.status} /></td>
                  <td className="p-2 text-xs">{o.user_name || '-'}</td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      <a href={`/sales/orders/${o.id}`} className="p-1 hover:bg-gray-700 rounded"><Eye className="h-3.5 w-3.5" /></a>
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
    </div>
  );
};

export default SalesOrderList;
