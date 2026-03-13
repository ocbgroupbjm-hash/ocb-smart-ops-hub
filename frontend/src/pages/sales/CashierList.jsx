import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Eye, Printer, Trash2, Loader2, RefreshCw, ShoppingCart, Edit2, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';
import ERPActionToolbar from '../../components/ERPActionToolbar';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

const CashierList = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [filters, setFilters] = useState({ keyword: '', dateFrom: '', dateTo: '', showPending: false });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api('/api/pos/transactions');
      if (res.ok) setTransactions((await res.json()).items || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredTransactions = useMemo(() => {
    return transactions.filter(t => {
      if (filters.keyword) {
        const kw = filters.keyword.toLowerCase();
        if (!t.transaction_number?.toLowerCase().includes(kw) && !t.customer_name?.toLowerCase().includes(kw)) return false;
      }
      if (filters.showPending && t.status !== 'pending') return false;
      return true;
    });
  }, [transactions, filters]);

  const summary = useMemo(() => {
    return filteredTransactions.reduce((acc, t) => ({
      count: acc.count + 1, total: acc.total + (t.total || 0),
    }), { count: 0, total: 0 });
  }, [filteredTransactions]);

  const handleEdit = (item) => { toast.info('Edit transaksi kasir akan segera tersedia'); };
  const handleDelete = async (item) => {
    if (item.status === 'completed') { toast.error('Transaksi selesai tidak bisa dihapus'); return; }
    if (!confirm(`Hapus transaksi ${item.transaction_number}?`)) return;
    try {
      const res = await api(`/api/pos/transactions/${item.id}`, { method: 'DELETE' });
      if (res.ok) { toast.success('Transaksi berhasil dihapus'); setSelectedItem(null); loadData(); }
    } catch { toast.error('Gagal menghapus'); }
  };
  const handlePrint = (item) => { toast.info(`Mencetak ${item.transaction_number}...`); };
  const handleReturn = (item) => { window.location.href = `/sales/returns/add?transaction_id=${item.id}`; };
  const handleRowSelect = (item) => { setSelectedItem(selectedItem?.id === item.id ? null : item); };

  return (
    <div className="space-y-4 p-4" data-testid="cashier-list-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2"><ShoppingCart className="h-6 w-6" /> Daftar Kasir</h1>
          <p className="text-gray-400 text-sm">Riwayat transaksi kasir/POS</p>
        </div>
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
            <label className="block text-xs text-gray-400 mb-1">Dari Tanggal</label>
            <input type="date" value={filters.dateFrom} onChange={e => setFilters(p => ({...p, dateFrom: e.target.value}))} className="w-full px-3 py-1.5 bg-[#0a0608] border border-red-900/30 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sampai Tanggal</label>
            <input type="date" value={filters.dateTo} onChange={e => setFilters(p => ({...p, dateTo: e.target.value}))} className="w-full px-3 py-1.5 bg-[#0a0608] border border-red-900/30 rounded text-sm text-white" />
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={filters.showPending} onChange={e => setFilters(p => ({...p, showPending: e.target.checked}))} className="rounded" /> Hanya Pending</label>
          </div>
          <div className="flex items-end">
            <button onClick={loadData} className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2 text-sm"><RefreshCw className="h-4 w-4" /> Refresh</button>
          </div>
        </div>
      </div>

      {/* TOOLBAR STANDAR ERP */}
      <ERPActionToolbar module="pos" selectedItem={selectedItem}
        onAdd={() => { window.location.href = '/kasir'; }}
        onEdit={(item) => handleEdit(item)}
        onDelete={(item) => handleDelete(item)}
        onPrint={(item) => handlePrint(item)}
        onReturn={(item) => handleReturn(item)}
        addLabel="Tambah Transaksi" editLabel="Edit" deleteLabel="Hapus"
      />

      <div className="bg-[#1a1214] rounded-lg border border-red-900/30 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-red-900/20">
              <tr className="text-left text-amber-200 text-xs">
                <th className="p-2 border-b border-red-900/30 w-10"><input type="checkbox" className="w-3 h-3" disabled /></th>
                <th className="p-2 border-b border-red-900/30">No Transaksi</th>
                <th className="p-2 border-b border-red-900/30">Tanggal</th>
                <th className="p-2 border-b border-red-900/30">Kd Pelanggan</th>
                <th className="p-2 border-b border-red-900/30">Nama</th>
                <th className="p-2 border-b border-red-900/30">Sales</th>
                <th className="p-2 border-b border-red-900/30">Keterangan</th>
                <th className="p-2 border-b border-red-900/30 text-right">Total</th>
                <th className="p-2 border-b border-red-900/30">Status</th>
                <th className="p-2 border-b border-red-900/30">User</th>
                <th className="p-2 border-b border-red-900/30">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan="11" className="p-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></td></tr>
              ) : filteredTransactions.length === 0 ? (
                <tr><td colSpan="11" className="p-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : filteredTransactions.map((t, idx) => (
                <tr key={t.id} onClick={() => handleRowSelect(t)}
                  className={`cursor-pointer transition-colors ${selectedItem?.id === t.id ? 'bg-amber-900/30 border-l-2 border-amber-500' : 'hover:bg-red-900/10'}`}
                  data-testid={`cashier-row-${idx}`}>
                  <td className="p-2 text-center"><input type="radio" checked={selectedItem?.id === t.id} onChange={() => handleRowSelect(t)} className="w-3 h-3 accent-amber-500" /></td>
                  <td className="p-2 text-blue-400 font-medium">{t.transaction_number}</td>
                  <td className="p-2">{formatDate(t.created_at)}</td>
                  <td className="p-2 font-mono text-xs">{t.customer_code || 'UMUM'}</td>
                  <td className="p-2">{t.customer_name || 'Cash/Umum'}</td>
                  <td className="p-2">{t.sales_person_name || '-'}</td>
                  <td className="p-2 text-xs">{t.notes || '-'}</td>
                  <td className="p-2 text-right font-medium">{formatRupiah(t.total)}</td>
                  <td className="p-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${t.status === 'completed' ? 'bg-green-600/20 text-green-300' : 'bg-yellow-600/20 text-yellow-300'}`}>
                      {t.status === 'completed' ? 'Selesai' : 'Pending'}
                    </span>
                  </td>
                  <td className="p-2 text-xs">{t.user_name || '-'}</td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      <button onClick={(e) => { e.stopPropagation(); }} className="p-1 hover:bg-gray-700 rounded"><Eye className="h-3.5 w-3.5" /></button>
                      <button onClick={(e) => { e.stopPropagation(); handlePrint(t); }} className="p-1 hover:bg-gray-700 rounded"><Printer className="h-3.5 w-3.5" /></button>
                      <button onClick={(e) => { e.stopPropagation(); handleEdit(t); }} className="p-1 hover:bg-purple-700 rounded text-purple-400"><Edit2 className="h-3.5 w-3.5" /></button>
                      <button onClick={(e) => { e.stopPropagation(); handleReturn(t); }} className="p-1 hover:bg-rose-700 rounded text-rose-400"><RotateCcw className="h-3.5 w-3.5" /></button>
                      <button onClick={(e) => { e.stopPropagation(); handleDelete(t); }} className="p-1 hover:bg-red-700 rounded text-red-400"><Trash2 className="h-3.5 w-3.5" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-[#1a1214] rounded-lg border border-red-900/30 p-3">
        <div className="grid grid-cols-2 gap-4 text-sm text-center">
          <div><p className="text-gray-400 text-xs">Jumlah Transaksi</p><p className="font-bold text-lg">{summary.count}</p></div>
          <div><p className="text-gray-400 text-xs">Total Penjualan</p><p className="font-bold text-lg text-blue-400">{formatRupiah(summary.total)}</p></div>
        </div>
      </div>
    </div>
  );
};

export default CashierList;
