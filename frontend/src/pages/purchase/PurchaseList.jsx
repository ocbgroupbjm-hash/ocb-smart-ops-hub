import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Search, Eye, Printer, Loader2, Download, Edit2, Trash2, Package } from 'lucide-react';
import { toast } from 'sonner';
import ERPActionToolbar from '../../components/ERPActionToolbar';

const PurchaseList = () => {
  const { api } = useAuth();
  const [purchases, setPurchases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  const loadPurchases = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(statusFilter && { status: statusFilter }),
        ...(dateFrom && { date_from: dateFrom }),
        ...(dateTo && { date_to: dateTo })
      });
      const res = await api(`/api/purchase/orders?${params}`);
      if (res.ok) {
        const data = await res.json();
        setPurchases(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm, statusFilter, dateFrom, dateTo]);

  useEffect(() => { loadPurchases(); }, [loadPurchases]);

  const getStatusBadge = (status) => {
    const badges = {
      draft: 'bg-gray-600/20 text-gray-400',
      submitted: 'bg-blue-600/20 text-blue-400',
      partial: 'bg-yellow-600/20 text-yellow-400',
      received: 'bg-green-600/20 text-green-400',
      cancelled: 'bg-red-600/20 text-red-400'
    };
    const labels = { draft: 'Draft', submitted: 'Disubmit', partial: 'Sebagian', received: 'Diterima', cancelled: 'Dibatalkan' };
    return <span className={`px-2 py-1 rounded-full text-xs ${badges[status] || badges.draft}`}>{labels[status] || status}</span>;
  };

  const handleView = (item) => { setSelectedItem(item); setShowDetail(true); };
  const handleEdit = (item) => { window.location.href = `/purchase/orders/edit/${item.id}`; };
  const handleDelete = async (item) => {
    if (item.status !== 'draft') { toast.error('Hanya PO Draft yang bisa dihapus'); return; }
    if (!confirm(`Hapus PO ${item.po_number}?`)) return;
    try {
      const res = await api(`/api/purchase/orders/${item.id}`, { method: 'DELETE' });
      if (res.ok) { toast.success('PO berhasil dihapus'); setSelectedItem(null); loadPurchases(); }
    } catch { toast.error('Gagal menghapus'); }
  };
  const handlePrint = (item) => { toast.info(`Mencetak ${item.po_number}...`); };
  const handleReceive = (item) => { window.location.href = `/purchase/receive/${item.id}`; };
  const handleRowSelect = (item) => { setSelectedItem(selectedItem?.id === item.id ? null : item); };
  
  // PRIORITAS 4: Export Pembelian to Excel
  const exportToExcel = async () => {
    try {
      toast.info('Mempersiapkan export...');
      
      const params = new URLSearchParams();
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      if (statusFilter) params.append('status', statusFilter);
      
      const res = await api(`/api/export/purchase?${params}`);
      
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pembelian_${new Date().toISOString().slice(0,10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success('Export berhasil!');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal export data');
      }
    } catch (err) {
      console.error('Export error:', err);
      toast.error('Gagal export data');
    }
  };

  return (
    <div className="space-y-4" data-testid="purchase-list-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Daftar Pembelian</h1>
          <p className="text-gray-400 text-sm">Riwayat semua transaksi pembelian</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input type="text" placeholder="Cari no. PO, supplier..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
          </div>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200">
            <option value="">Semua Status</option>
            <option value="draft">Draft</option>
            <option value="submitted">Disubmit</option>
            <option value="partial">Sebagian Diterima</option>
            <option value="received">Diterima</option>
            <option value="cancelled">Dibatalkan</option>
          </select>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
        </div>
      </div>

      {/* TOOLBAR STANDAR ERP */}
      <ERPActionToolbar
        module="purchase"
        selectedItem={selectedItem}
        onAdd={() => { window.location.href = '/purchase/orders'; }}
        onEdit={(item) => handleEdit(item)}
        onDelete={(item) => handleDelete(item)}
        onPrint={(item) => handlePrint(item)}
        onReceive={(item) => handleReceive(item)}
        onExport={exportToExcel}
        addLabel="Tambah Pembelian"
        editLabel="Edit"
        deleteLabel="Hapus"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total PO</p>
          <p className="text-2xl font-bold text-amber-200">{purchases.length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Menunggu</p>
          <p className="text-2xl font-bold text-blue-400">{purchases.filter(p => p.status === 'submitted').length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Diterima</p>
          <p className="text-2xl font-bold text-green-400">{purchases.filter(p => p.status === 'received').length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total Nilai</p>
          <p className="text-xl font-bold text-green-400">Rp {purchases.reduce((sum, p) => sum + (p.total || 0), 0).toLocaleString('id-ID')}</p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-3 py-3 text-center text-xs font-semibold text-amber-200 w-10">
                  <input type="checkbox" className="w-3 h-3" disabled />
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. PO</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">SUPPLIER</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">ITEMS</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">TOTAL</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : purchases.length === 0 ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Belum ada data pembelian</td></tr>
              ) : purchases.map((item, idx) => (
                <tr key={item.id} onClick={() => handleRowSelect(item)}
                  className={`cursor-pointer transition-colors ${selectedItem?.id === item.id ? 'bg-amber-900/30 border-l-2 border-amber-500' : 'hover:bg-red-900/10'}`}
                  data-testid={`purchase-row-${idx}`}>
                  <td className="px-3 py-3 text-center">
                    <input type="radio" checked={selectedItem?.id === item.id} onChange={() => handleRowSelect(item)} className="w-3 h-3 accent-amber-500" />
                  </td>
                  <td className="px-4 py-3 font-medium text-amber-300 font-mono">{item.po_number}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">{new Date(item.created_at).toLocaleDateString('id-ID')}</td>
                  <td className="px-4 py-3 text-sm text-gray-200">{item.supplier_name}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-300">{item.items?.length || 0} item</td>
                  <td className="px-4 py-3 text-sm text-right text-green-400 font-medium">Rp {(item.total || 0).toLocaleString('id-ID')}</td>
                  <td className="px-4 py-3 text-center">{getStatusBadge(item.status)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button onClick={(e) => { e.stopPropagation(); handleView(item); }} className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400"><Eye className="h-4 w-4" /></button>
                      <button onClick={(e) => { e.stopPropagation(); handlePrint(item); }} className="p-1.5 hover:bg-gray-600/20 rounded text-gray-400"><Printer className="h-4 w-4" /></button>
                      <button onClick={(e) => { e.stopPropagation(); handleEdit(item); }} className="p-1.5 hover:bg-purple-600/20 rounded text-purple-400"><Edit2 className="h-4 w-4" /></button>
                      <button onClick={(e) => { e.stopPropagation(); handleDelete(item); }} className="p-1.5 hover:bg-red-600/20 rounded text-red-400"><Trash2 className="h-4 w-4" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Modal */}
      {showDetail && selectedItem && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-amber-100">Detail Pembelian</h2>
                <p className="text-sm text-gray-400">{selectedItem.po_number}</p>
              </div>
              <button onClick={() => setShowDetail(false)} className="p-2 hover:bg-red-900/20 rounded text-gray-400">✕</button>
            </div>
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><p className="text-sm text-gray-400">Supplier</p><p className="text-gray-200">{selectedItem.supplier_name}</p></div>
                <div><p className="text-sm text-gray-400">Tanggal</p><p className="text-gray-200">{new Date(selectedItem.created_at).toLocaleDateString('id-ID')}</p></div>
                <div><p className="text-sm text-gray-400">Status</p>{getStatusBadge(selectedItem.status)}</div>
                <div><p className="text-sm text-gray-400">Total</p><p className="text-green-400 font-bold">Rp {(selectedItem.total || 0).toLocaleString('id-ID')}</p></div>
              </div>
              <div className="border-t border-red-900/30 pt-4">
                <h3 className="text-sm font-semibold text-amber-200 mb-2">Item Pembelian</h3>
                <table className="w-full">
                  <thead className="bg-red-900/20"><tr>
                    <th className="px-3 py-2 text-left text-xs text-gray-400">PRODUK</th>
                    <th className="px-3 py-2 text-center text-xs text-gray-400">QTY</th>
                    <th className="px-3 py-2 text-right text-xs text-gray-400">HARGA</th>
                    <th className="px-3 py-2 text-right text-xs text-gray-400">SUBTOTAL</th>
                  </tr></thead>
                  <tbody className="divide-y divide-red-900/20">
                    {selectedItem.items?.map((itm, idx) => (
                      <tr key={idx}>
                        <td className="px-3 py-2 text-gray-200">{itm.product_name}</td>
                        <td className="px-3 py-2 text-center text-gray-400">{itm.quantity}</td>
                        <td className="px-3 py-2 text-right text-gray-400">Rp {(itm.unit_cost || 0).toLocaleString('id-ID')}</td>
                        <td className="px-3 py-2 text-right text-green-400">Rp {((itm.quantity || 0) * (itm.unit_cost || 0)).toLocaleString('id-ID')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PurchaseList;
