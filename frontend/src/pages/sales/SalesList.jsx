import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Plus, Search, Eye, Printer, Trash2, Loader2, RefreshCw, Edit, Edit2, RotateCcw
} from 'lucide-react';
import { toast } from 'sonner';
import { OwnerEditButton, OwnerEditModal } from '../../components/OwnerEditButton';
import ERPActionToolbar from '../../components/ERPActionToolbar';

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
  const [selectedItem, setSelectedItem] = useState(null);
  
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

  // CRUD handlers
  const handleEdit = (item) => {
    // Navigate to edit page or open modal
    setEditItem(item);
    setShowOwnerEdit(true);
  };

  const handleDelete = async (item) => {
    if (item.status === 'completed') {
      toast.error('Invoice yang sudah selesai tidak bisa dihapus');
      return;
    }
    if (!confirm(`Hapus invoice ${item.invoice_number}?`)) return;
    try {
      const res = await api(`/api/sales/invoices/${item.id}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Invoice berhasil dihapus');
        setSelectedItem(null);
        loadData();
      }
    } catch (err) {
      toast.error('Gagal menghapus invoice');
    }
  };

  const handlePrint = (item) => {
    toast.info(`Mencetak invoice ${item.invoice_number}...`);
    window.print();
  };

  const handleReturn = (item) => {
    // Navigate to return page
    window.location.href = `/sales/return/add?invoice_id=${item.id}`;
  };

  const handleRowSelect = (item) => {
    if (selectedItem?.id === item.id) {
      setSelectedItem(null);
    } else {
      setSelectedItem(item);
    }
  };

  return (
    <div className="space-y-4 p-4" data-testid="sales-list-page">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-amber-100">Daftar Penjualan</h2>
          <p className="text-gray-400 text-sm">Kelola transaksi penjualan</p>
        </div>
      </div>

      {/* Filters */}
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
            <label className="block text-xs text-gray-400 mb-1">Dept / Gudang</label>
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
            <button onClick={loadData} className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2 text-sm">
              <RefreshCw className="h-4 w-4" /> Refresh
            </button>
          </div>
        </div>
      </div>

      {/* TOOLBAR STANDAR ERP */}
      <ERPActionToolbar
        module="sales"
        selectedItem={selectedItem}
        onAdd={() => { window.location.href = '/sales/add'; }}
        onEdit={(item) => handleEdit(item)}
        onDelete={(item) => handleDelete(item)}
        onPrint={(item) => handlePrint(item)}
        onReturn={(item) => handleReturn(item)}
        addLabel="Tambah Invoice"
        editLabel="Edit Invoice"
        deleteLabel="Hapus Invoice"
      />

      {/* Table */}
      <div className="bg-[#1a1214] rounded-lg border border-red-900/30 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-red-900/20">
              <tr className="text-left text-amber-200 text-xs">
                <th className="p-2 border-b border-red-900/30 w-10">
                  <input type="checkbox" className="w-3 h-3" disabled />
                </th>
                <th className="p-2 border-b border-red-900/30">No Transaksi</th>
                <th className="p-2 border-b border-red-900/30">Tanggal</th>
                <th className="p-2 border-b border-red-900/30">Kd Pelanggan</th>
                <th className="p-2 border-b border-red-900/30">Nama</th>
                <th className="p-2 border-b border-red-900/30">Sales</th>
                <th className="p-2 border-b border-red-900/30">No Faktur Pajak</th>
                <th className="p-2 border-b border-red-900/30">Keterangan</th>
                <th className="p-2 border-b border-red-900/30 text-right">Total</th>
                <th className="p-2 border-b border-red-900/30">Status</th>
                <th className="p-2 border-b border-red-900/30">User</th>
                <th className="p-2 border-b border-red-900/30">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan="12" className="p-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></td></tr>
              ) : filteredSales.length === 0 ? (
                <tr><td colSpan="12" className="p-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : filteredSales.map((s, idx) => (
                <tr 
                  key={s.id} 
                  onClick={() => handleRowSelect(s)}
                  className={`cursor-pointer transition-colors ${
                    selectedItem?.id === s.id 
                      ? 'bg-amber-900/30 border-l-2 border-amber-500' 
                      : 'hover:bg-red-900/10'
                  }`}
                  data-testid={`sales-row-${idx}`}
                >
                  <td className="p-2 text-center">
                    <input 
                      type="radio" 
                      checked={selectedItem?.id === s.id}
                      onChange={() => handleRowSelect(s)}
                      className="w-3 h-3 accent-amber-500"
                    />
                  </td>
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
                      <a href={`/sales/${s.id}`} onClick={(e) => e.stopPropagation()} className="p-1 hover:bg-gray-700 rounded" title="Lihat">
                        <Eye className="h-3.5 w-3.5" />
                      </a>
                      <button onClick={(e) => { e.stopPropagation(); handlePrint(s); }} className="p-1 hover:bg-gray-700 rounded" title="Print">
                        <Printer className="h-3.5 w-3.5" />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); handleEdit(s); }} className="p-1 hover:bg-purple-700 rounded text-purple-400" title="Edit">
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); handleDelete(s); }} className="p-1 hover:bg-red-700 rounded text-red-400" title="Hapus">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
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
      <div className="bg-[#1a1214] rounded-lg border border-red-900/30 p-3">
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
