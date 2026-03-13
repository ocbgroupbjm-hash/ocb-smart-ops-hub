import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Plus, Search, Eye, Printer, Trash2, Loader2, RefreshCw, Edit
} from 'lucide-react';
import { toast } from 'sonner';
import { OwnerEditButton, OwnerEditModal } from '../../components/OwnerEditButton';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

const StatusBadge = ({ status }) => {
  const styles = {
    draft: 'bg-gray-600/20 text-gray-300',
    completed: 'bg-green-600/20 text-green-300',
    cancelled: 'bg-red-600/20 text-red-300',
  };
  return <span className={`px-2 py-0.5 rounded text-xs ${styles[status] || styles.draft}`}>{status?.toUpperCase() || 'N/A'}</span>;
};

const SalesList = () => {
  const { api, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [sales, setSales] = useState([]);
  const [filters, setFilters] = useState({ keyword: '', dateFrom: '', dateTo: '', warehouse_id: '' });
  const [warehouses, setWarehouses] = useState([]);
  
  // Owner edit states
  const [showOwnerEdit, setShowOwnerEdit] = useState(false);
  const [editItem, setEditItem] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [salesRes, whRes] = await Promise.all([
        api('/api/sales/invoices'),
        api('/api/master/warehouses')
      ]);
      if (salesRes.ok) setSales((await salesRes.json()).items || []);
      if (whRes.ok) setWarehouses(await whRes.json() || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredSales = useMemo(() => {
    return sales.filter(s => {
      if (filters.keyword) {
        const kw = filters.keyword.toLowerCase();
        if (!s.invoice_number?.toLowerCase().includes(kw) && 
            !s.customer_name?.toLowerCase().includes(kw)) return false;
      }
      return true;
    });
  }, [sales, filters]);

  // Calculate summary
  const summary = useMemo(() => {
    return filteredSales.reduce((acc, s) => ({
      count: acc.count + 1,
      total: acc.total + (s.total || 0),
      paid: acc.paid + (s.paid_amount || 0),
    }), { count: 0, total: 0, paid: 0 });
  }, [filteredSales]);

  return (
    <div className="space-y-4 p-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">Daftar Penjualan</h2>
        <a href="/sales/add" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2 text-sm">
          <Plus className="h-4 w-4" /> Tambah
        </a>
      </div>

      {/* Filters */}
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
            <label className="block text-xs text-gray-400 mb-1">Dept / Gudang</label>
            <select value={filters.warehouse_id} onChange={e => setFilters(p => ({...p, warehouse_id: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white">
              <option value="">Semua</option>
              {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
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
                <th className="p-2 border-b border-gray-700">Sales</th>
                <th className="p-2 border-b border-gray-700">No Faktur Pajak</th>
                <th className="p-2 border-b border-gray-700">Keterangan</th>
                <th className="p-2 border-b border-gray-700 text-right">Total</th>
                <th className="p-2 border-b border-gray-700">Status</th>
                <th className="p-2 border-b border-gray-700">User</th>
                <th className="p-2 border-b border-gray-700">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {loading ? (
                <tr><td colSpan="11" className="p-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></td></tr>
              ) : filteredSales.length === 0 ? (
                <tr><td colSpan="11" className="p-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : filteredSales.map(s => (
                <tr key={s.id} className="hover:bg-gray-800/30">
                  <td className="p-2 text-blue-400 font-medium">{s.invoice_number}</td>
                  <td className="p-2">{formatDate(s.created_at)}</td>
                  <td className="p-2 font-mono text-xs">{s.customer_code || '-'}</td>
                  <td className="p-2">{s.customer_name}</td>
                  <td className="p-2">{s.sales_person_name || '-'}</td>
                  <td className="p-2 text-xs">{s.tax_invoice_number || '-'}</td>
                  <td className="p-2 text-xs">{s.notes || '-'}</td>
                  <td className="p-2 text-right font-medium">{formatRupiah(s.total)}</td>
                  <td className="p-2"><StatusBadge status={s.status} /></td>
                  <td className="p-2 text-xs">{s.user_name || '-'}</td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      <a href={`/sales/${s.id}`} className="p-1 hover:bg-gray-700 rounded"><Eye className="h-3.5 w-3.5" /></a>
                      <button className="p-1 hover:bg-gray-700 rounded"><Printer className="h-3.5 w-3.5" /></button>
                      {/* Owner Edit Button */}
                      <OwnerEditButton
                        item={s}
                        module="sales"
                        onEdit={(item) => { setEditItem(item); setShowOwnerEdit(true); }}
                        size="sm"
                        showLabel={false}
                      />
                      <button className="p-1 hover:bg-red-700 rounded"><Trash2 className="h-3.5 w-3.5 text-red-400" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Owner Edit Modal */}
      <OwnerEditModal
        isOpen={showOwnerEdit}
        onClose={() => { setShowOwnerEdit(false); setEditItem(null); }}
        module="sales"
        item={editItem}
        fields={[
          { name: 'notes', label: 'Catatan', type: 'textarea' },
          { name: 'discount_amount', label: 'Potongan (Rp)', type: 'number' }
        ]}
        onSave={() => { setShowOwnerEdit(false); setEditItem(null); loadData(); }}
      />

      {/* Summary */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="grid grid-cols-3 gap-4 text-sm text-center">
          <div>
            <p className="text-gray-400 text-xs">Jumlah Transaksi</p>
            <p className="font-bold text-lg">{summary.count}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs">Total Penjualan</p>
            <p className="font-bold text-lg text-blue-400">{formatRupiah(summary.total)}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs">Total Dibayar</p>
            <p className="font-bold text-lg text-green-400">{formatRupiah(summary.paid)}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SalesList;
