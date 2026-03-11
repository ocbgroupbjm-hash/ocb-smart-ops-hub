import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Search, Loader2, FileSpreadsheet, Download, Check, X
} from 'lucide-react';
import { toast } from 'sonner';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

const TaxExport = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(false);
  const [invoices, setInvoices] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [filters, setFilters] = useState({
    format: 'xml',
    invoice_type: 'all',
    date_from: '',
    date_to: '',
    customer_from: '',
    customer_to: '',
    warehouse_id: '',
    show_taxable: 'all',
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      params.append('has_tax', 'true');
      
      const res = await api(`/api/sales/invoices?${params}`);
      if (res.ok) {
        const data = await res.json();
        setInvoices((data.items || []).filter(i => i.tax_amount > 0 || filters.show_taxable === 'all'));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [api, filters]);

  const toggleSelect = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (selectedIds.length === invoices.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(invoices.map(i => i.id));
    }
  };

  const exportCSV = async () => {
    if (selectedIds.length === 0) {
      toast.error('Pilih minimal 1 faktur');
      return;
    }
    
    try {
      const res = await api('/api/sales/tax-export/csv', {
        method: 'POST',
        body: JSON.stringify({ invoice_ids: selectedIds })
      });
      
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `faktur_pajak_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
        toast.success('Export CSV berhasil');
      } else {
        toast.error('Gagal export CSV');
      }
    } catch (err) {
      console.error(err);
      toast.error('Error export');
    }
  };

  const exportXML = async () => {
    if (selectedIds.length === 0) {
      toast.error('Pilih minimal 1 faktur');
      return;
    }
    
    try {
      const res = await api('/api/sales/tax-export/xml', {
        method: 'POST',
        body: JSON.stringify({ invoice_ids: selectedIds })
      });
      
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `faktur_pajak_${new Date().toISOString().slice(0,10)}.xml`;
        a.click();
        toast.success('Export XML berhasil');
      } else {
        toast.error('Gagal export XML');
      }
    } catch (err) {
      console.error(err);
      toast.error('Error export');
    }
  };

  return (
    <div className="space-y-4 p-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <FileSpreadsheet className="h-5 w-5 text-blue-400" />
          Laporan CSV/XML Faktur Pajak Keluaran
        </h2>
      </div>

      {/* Filters */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4">
        <div className="grid grid-cols-4 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Format</label>
            <select value={filters.format} onChange={e => setFilters(p => ({...p, format: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white">
              <option value="xml">XML</option>
              <option value="csv">CSV</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Jenis Faktur</label>
            <select value={filters.invoice_type} onChange={e => setFilters(p => ({...p, invoice_type: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white">
              <option value="all">Semua</option>
              <option value="standard">Standar</option>
              <option value="replacement">Pengganti</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Periode Dari</label>
            <input type="date" value={filters.date_from} onChange={e => setFilters(p => ({...p, date_from: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sampai</label>
            <input type="date" value={filters.date_to} onChange={e => setFilters(p => ({...p, date_to: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
          </div>
        </div>
        
        <div className="grid grid-cols-4 gap-4 mt-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tampilkan</label>
            <select value={filters.show_taxable} onChange={e => setFilters(p => ({...p, show_taxable: e.target.value}))} className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white">
              <option value="all">Semua Data</option>
              <option value="taxable">Kena Pajak Saja</option>
              <option value="non_taxable">Tidak Kena Pajak</option>
            </select>
          </div>
          <div className="col-span-2"></div>
          <div className="flex items-end">
            <button onClick={loadData} className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2 text-sm w-full justify-center">
              <Search className="h-4 w-4" /> Tampil Data
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 sticky top-0">
              <tr className="text-left text-gray-400 text-xs">
                <th className="p-2 border-b border-gray-700 w-10">
                  <input type="checkbox" checked={selectedIds.length === invoices.length && invoices.length > 0} onChange={selectAll} className="rounded" />
                </th>
                <th className="p-2 border-b border-gray-700">No Transaksi</th>
                <th className="p-2 border-b border-gray-700">Tanggal</th>
                <th className="p-2 border-b border-gray-700">Pelanggan</th>
                <th className="p-2 border-b border-gray-700">NPWP</th>
                <th className="p-2 border-b border-gray-700">Nama NPWP</th>
                <th className="p-2 border-b border-gray-700">Alamat NPWP</th>
                <th className="p-2 border-b border-gray-700 text-right">PPN</th>
                <th className="p-2 border-b border-gray-700">No Faktur</th>
                <th className="p-2 border-b border-gray-700 text-right">Total</th>
                <th className="p-2 border-b border-gray-700">User</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {loading ? (
                <tr><td colSpan="11" className="p-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></td></tr>
              ) : invoices.length === 0 ? (
                <tr><td colSpan="11" className="p-8 text-center text-gray-400">Klik "Tampil Data" untuk memuat faktur</td></tr>
              ) : invoices.map(inv => (
                <tr key={inv.id} className={`hover:bg-gray-800/30 ${selectedIds.includes(inv.id) ? 'bg-blue-900/20' : ''}`}>
                  <td className="p-2">
                    <input type="checkbox" checked={selectedIds.includes(inv.id)} onChange={() => toggleSelect(inv.id)} className="rounded" />
                  </td>
                  <td className="p-2 text-blue-400">{inv.invoice_number}</td>
                  <td className="p-2">{formatDate(inv.created_at)}</td>
                  <td className="p-2">{inv.customer_name}</td>
                  <td className="p-2 font-mono text-xs">{inv.customer_npwp || '-'}</td>
                  <td className="p-2 text-xs">{inv.customer_npwp_name || inv.customer_name}</td>
                  <td className="p-2 text-xs truncate max-w-32">{inv.customer_address || '-'}</td>
                  <td className="p-2 text-right">{formatRupiah(inv.tax_amount)}</td>
                  <td className="p-2 font-mono text-xs">{inv.tax_invoice_number || '-'}</td>
                  <td className="p-2 text-right font-medium">{formatRupiah(inv.total)}</td>
                  <td className="p-2 text-xs">{inv.user_name || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Actions */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4">
        <div className="flex justify-between items-center">
          <div className="flex gap-2">
            <button onClick={selectAll} className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded text-sm">
              {selectedIds.length === invoices.length ? 'Tidak Pilih' : 'Pilih Semua'}
            </button>
            <span className="text-sm text-gray-400 py-2">
              {selectedIds.length} faktur dipilih
            </span>
          </div>
          <div className="flex gap-2">
            <button onClick={exportCSV} className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded flex items-center gap-2 text-sm">
              <Download className="h-4 w-4" /> Export CSV
            </button>
            <button onClick={exportXML} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2 text-sm">
              <Download className="h-4 w-4" /> Export XML
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaxExport;
