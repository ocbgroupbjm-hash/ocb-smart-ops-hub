import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Eye, Printer, Trash2, Loader2, RefreshCw, FileText, Edit2, Check } from 'lucide-react';
import { toast } from 'sonner';
import ERPActionToolbar from '../../components/ERPActionToolbar';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

const StatusBadge = ({ status }) => {
  const styles = {
    draft: 'bg-gray-600/20 text-gray-300', pending: 'bg-yellow-600/20 text-yellow-300',
    confirmed: 'bg-blue-600/20 text-blue-300', completed: 'bg-green-600/20 text-green-300', cancelled: 'bg-red-600/20 text-red-300',
  };
  const labels = { draft: 'Draft', pending: 'Pending', confirmed: 'Confirmed', completed: 'Selesai', cancelled: 'Batal' };
  return <span className={`px-2 py-0.5 rounded text-xs ${styles[status] || styles.draft}`}>{labels[status] || status?.toUpperCase() || 'N/A'}</span>;
};

const SalesOrderList = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [filters, setFilters] = useState({ keyword: '', dateFrom: '', dateTo: '', warehouse_id: '' });
  const [warehouses, setWarehouses] = useState([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [ordersRes, whRes] = await Promise.all([api('/api/sales/orders'), api('/api/master/warehouses')]);
      if (ordersRes.ok) setOrders((await ordersRes.json()).items || []);
      if (whRes.ok) setWarehouses(await whRes.json() || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredOrders = useMemo(() => {
    return orders.filter(o => {
      if (filters.keyword) {
        const kw = filters.keyword.toLowerCase();
        if (!o.order_number?.toLowerCase().includes(kw) && !o.customer_name?.toLowerCase().includes(kw)) return false;
      }
      return true;
    });
  }, [orders, filters]);

  const handleEdit = (item) => { window.location.href = `/sales/orders/edit/${item.id}`; };
  const handleDelete = async (item) => {
    if (item.status !== 'draft') { toast.error('Hanya pesanan Draft yang bisa dihapus'); return; }
    if (!confirm(`Hapus pesanan ${item.order_number}?`)) return;
    try {
      const res = await api(`/api/sales/orders/${item.id}`, { method: 'DELETE' });
      if (res.ok) { toast.success('Pesanan berhasil dihapus'); setSelectedItem(null); loadData(); }
    } catch { toast.error('Gagal menghapus'); }
  };
  const handlePrint = (item) => { toast.info(`Mencetak ${item.order_number}...`); };
  const handleApprove = async (item) => {
    if (!confirm(`Konfirmasi pesanan ${item.order_number}?`)) return;
    try {
      const res = await api(`/api/sales/orders/${item.id}/confirm`, { method: 'POST' });
      if (res.ok) { toast.success('Pesanan dikonfirmasi'); loadData(); }
    } catch { toast.error('Gagal mengkonfirmasi'); }
  };
  const handleRowSelect = (item) => { setSelectedItem(selectedItem?.id === item.id ? null : item); };

  return (
    <div className="space-y-4 p-4" data-testid="sales-orders-page">
      <div className="flex justify-between items-center">
        <div><h1 className="text-2xl font-bold text-amber-100">Pesanan Jual</h1><p className="text-gray-400 text-sm">Kelola pesanan penjualan</p></div>
      </div>

      <div className="bg-[#1a1214] rounded-lg border border-red-900/30 p-3">
        <div className="grid grid-cols-5 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Kata Kunci</label>
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />
              <input type="text" value={filters.keyword} onChange={e => setFilters(p => ({...p, keyword: e.target.value}))} placeholder="Cari..." className="w-full pl-8 pr-3 py-1.5 bg-[#0a0608] border border-red-900/30 rounded text-sm text-white" />
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Gudang</label>
            <select value={filters.warehouse_id} onChange={e => setFilters(p => ({...p, warehouse_id: e.target.value}))} className="w-full px-3 py-1.5 bg-[#0a0608] border border-red-900/30 rounded text-sm text-white">
              <option value="">Semua</option>
              {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Dari Tanggal</label>
            <input type="date" value={filters.dateFrom} onChange={e => setFilters(p => ({...p, dateFrom: e.target.value}))} className="w-full px-3 py-1.5 bg-[#0a0608] border border-red-900/30 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sampai Tanggal</label>
            <input type="date" value={filters.dateTo} onChange={e => setFilters(p => ({...p, dateTo: e.target.value}))} className="w-full px-3 py-1.5 bg-[#0a0608] border border-red-900/30 rounded text-sm text-white" />
          </div>
          <div className="flex items-end">
            <button onClick={loadData} className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2 text-sm"><RefreshCw className="h-4 w-4" /> Refresh</button>
          </div>
        </div>
      </div>

      {/* TOOLBAR STANDAR ERP */}
      <ERPActionToolbar module="sales_order" selectedItem={selectedItem}
        onAdd={() => { window.location.href = '/sales/orders/add'; }}
        onEdit={(item) => handleEdit(item)}
        onDelete={(item) => handleDelete(item)}
        onPrint={(item) => handlePrint(item)}
        onApprove={(item) => handleApprove(item)}
        addLabel="Tambah Pesanan" editLabel="Edit" deleteLabel="Hapus"
      />

      <div className="bg-[#1a1214] rounded-lg border border-red-900/30 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-red-900/20">
              <tr className="text-left text-amber-200 text-xs">
                <th className="p-2 border-b border-red-900/30 w-10"><input type="checkbox" className="w-3 h-3" disabled /></th>
                <th className="p-2 border-b border-red-900/30">No Transaksi</th>
                <th className="p-2 border-b border-red-900/30">Tanggal</th>
                <th className="p-2 border-b border-red-900/30">Tgl Kirim</th>
                <th className="p-2 border-b border-red-900/30">Kode Pelanggan</th>
                <th className="p-2 border-b border-red-900/30">Nama</th>
                <th className="p-2 border-b border-red-900/30 text-right">Total</th>
                <th className="p-2 border-b border-red-900/30">Status</th>
                <th className="p-2 border-b border-red-900/30">User</th>
                <th className="p-2 border-b border-red-900/30">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan="10" className="p-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></td></tr>
              ) : filteredOrders.length === 0 ? (
                <tr><td colSpan="10" className="p-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : filteredOrders.map((o, idx) => (
                <tr key={o.id} onClick={() => handleRowSelect(o)}
                  className={`cursor-pointer transition-colors ${selectedItem?.id === o.id ? 'bg-amber-900/30 border-l-2 border-amber-500' : 'hover:bg-red-900/10'}`}
                  data-testid={`order-row-${idx}`}>
                  <td className="p-2 text-center"><input type="radio" checked={selectedItem?.id === o.id} onChange={() => handleRowSelect(o)} className="w-3 h-3 accent-amber-500" /></td>
                  <td className="p-2 text-blue-400 font-medium">{o.order_number}</td>
                  <td className="p-2">{formatDate(o.created_at)}</td>
                  <td className="p-2">{formatDate(o.delivery_date)}</td>
                  <td className="p-2 font-mono text-xs">{o.customer_code || '-'}</td>
                  <td className="p-2">{o.customer_name}</td>
                  <td className="p-2 text-right font-medium">{formatRupiah(o.total)}</td>
                  <td className="p-2"><StatusBadge status={o.status} /></td>
                  <td className="p-2 text-xs">{o.user_name || '-'}</td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      <a href={`/sales/orders/${o.id}`} onClick={(e) => e.stopPropagation()} className="p-1 hover:bg-gray-700 rounded"><Eye className="h-3.5 w-3.5" /></a>
                      <button onClick={(e) => { e.stopPropagation(); handlePrint(o); }} className="p-1 hover:bg-gray-700 rounded"><Printer className="h-3.5 w-3.5" /></button>
                      <button onClick={(e) => { e.stopPropagation(); handleEdit(o); }} className="p-1 hover:bg-purple-700 rounded text-purple-400"><Edit2 className="h-3.5 w-3.5" /></button>
                      <button onClick={(e) => { e.stopPropagation(); handleDelete(o); }} className="p-1 hover:bg-red-700 rounded text-red-400"><Trash2 className="h-3.5 w-3.5" /></button>
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
