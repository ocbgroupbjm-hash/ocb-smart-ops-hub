import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { 
  Search, Eye, DollarSign, AlertTriangle, RefreshCw, 
  Filter, Download, Calendar, Building2, Clock,
  TrendingUp, TrendingDown, FileText, Wallet, Edit2, Trash2, Printer, Plus, RotateCcw, X
} from 'lucide-react';
import APDetailModal from '../../components/accounting/APDetailModal';
import APPaymentModal from '../../components/accounting/APPaymentModal';
import { toast } from 'sonner';
import { formatDateDisplay, isOverdue as checkOverdue } from '../../utils/dateUtils';

const API = process.env.REACT_APP_BACKEND_URL;

// OCB TITAN Design Tokens - Dark Enterprise Theme
const DESIGN = {
  text: {
    primary: 'text-[#E5E7EB]',
    secondary: 'text-[#9CA3AF]',
    accent: 'text-[#F97316]',
  },
  bg: {
    page: 'bg-[#0F172A]',
    card: 'bg-[#1E293B]',
    input: 'bg-[#0F172A]',
    hover: 'hover:bg-[#334155]',
    tableHeader: 'bg-[#0F172A]',
  },
  border: {
    default: 'border-[#334155]',
  }
};

const STATUS_CONFIG = {
  open: { label: 'Terbuka', bg: 'bg-blue-500/20', text: 'text-blue-400' },
  partial: { label: 'Sebagian', bg: 'bg-amber-500/20', text: 'text-amber-400' },
  paid: { label: 'Lunas', bg: 'bg-emerald-500/20', text: 'text-emerald-400' },
  overdue: { label: 'Jatuh Tempo', bg: 'bg-rose-500/20', text: 'text-rose-400' },
  draft: { label: 'Draft', bg: 'bg-slate-500/20', text: 'text-slate-400' },
  // TASK 1: New enterprise statuses
  void: { label: 'Void', bg: 'bg-gray-500/20', text: 'text-gray-400' },
  cancelled: { label: 'Dibatalkan', bg: 'bg-gray-500/20', text: 'text-gray-400' },
  reversed: { label: 'Dibalik', bg: 'bg-purple-500/20', text: 'text-purple-400' },
};

const formatCurrency = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  try {
    return new Date(dateStr).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return dateStr;
  }
};
const isOverdue = (dueDate) => {
  if (!dueDate) return false;
  try {
    return new Date(dueDate) < new Date();
  } catch {
    return false;
  }
};

export default function AccountsPayable() {
  const [apList, setApList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [aging, setAging] = useState(null);
  const [suppliers, setSuppliers] = useState([]);
  
  // Filters
  const [keyword, setKeyword] = useState('');
  const [supplierId, setSupplierId] = useState('');
  const [status, setStatus] = useState('');
  
  // Modals
  const [selectedAP, setSelectedAP] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [showPayment, setShowPayment] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  
  const token = localStorage.getItem('token');

  const fetchAPList = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (keyword) params.append('keyword', keyword);
      if (supplierId) params.append('supplier_id', supplierId);
      if (status) params.append('status', status);
      
      const res = await fetch(`${API}/api/ap/list?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setApList(data.items || []);
      }
    } catch (err) {
      console.error('Error fetching AP:', err);
    } finally {
      setLoading(false);
    }
  }, [token, keyword, supplierId, status]);

  const fetchSummary = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ap/summary/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSummary(data);
      }
    } catch (err) {
      console.error('Error fetching summary:', err);
    }
  }, [token]);

  const fetchAging = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ap/aging`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAging(data.aging);
      }
    } catch (err) {
      console.error('Error fetching aging:', err);
    }
  }, [token]);

  const fetchSuppliers = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/suppliers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSuppliers(data.items || data || []);
      }
    } catch (err) {
      console.error('Error fetching suppliers:', err);
    }
  }, [token]);

  useEffect(() => {
    fetchAPList();
    fetchSummary();
    fetchAging();
    fetchSuppliers();
  }, [fetchAPList, fetchSummary, fetchAging, fetchSuppliers]);

  const handleViewDetail = (ap) => {
    setSelectedAP(ap);
    setShowDetail(true);
  };

  const handlePayment = (ap) => {
    setSelectedAP(ap);
    setShowPayment(true);
  };

  const handleEdit = (ap) => {
    if (ap.status === 'paid') {
      toast.error('Hutang lunas tidak bisa diedit. Gunakan jurnal koreksi.');
      return;
    }
    if (ap.paid_amount > 0) {
      toast.error('Hutang dengan pembayaran tidak bisa diedit. Gunakan jurnal koreksi.');
      return;
    }
    setSelectedAP(ap);
    setShowEditModal(true);
  };

  const handleDeleteConfirm = (ap) => {
    if (ap.status === 'paid' || ap.paid_amount > 0) {
      toast.error('Tidak dapat menghapus hutang yang sudah ada pembayaran');
      return;
    }
    setSelectedAP(ap);
    setShowDeleteConfirm(true);
  };

  const handleSoftDelete = async () => {
    if (!selectedAP) return;
    
    setActionLoading(true);
    try {
      // TASK 1: Use VOID endpoint (enterprise flow)
      const res = await fetch(`${API}/api/ap/${selectedAP.id}/void`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        toast.success(data.message || 'Hutang berhasil di-VOID');
        setShowDeleteConfirm(false);
        setSelectedAP(null);
        fetchAPList();
        fetchSummary();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Gagal menghapus hutang');
      }
    } catch (err) {
      console.error('Delete error:', err);
      toast.error('Terjadi kesalahan saat menghapus');
    } finally {
      setActionLoading(false);
    }
  };

  const handlePrint = (ap) => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Bukti Hutang - ${ap.ap_no}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }
          .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 15px; margin-bottom: 20px; }
          .company { font-size: 18px; font-weight: bold; }
          .title { font-size: 16px; margin-top: 10px; }
          .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
          .info-item { padding: 10px; background: #f5f5f5; border-radius: 4px; }
          .label { font-size: 12px; color: #666; margin-bottom: 4px; }
          .value { font-size: 14px; font-weight: 500; }
          .amount-section { background: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; }
          .amount { font-size: 24px; font-weight: bold; color: #dc2626; }
          .footer { margin-top: 40px; display: flex; justify-content: space-between; }
          .signature { text-align: center; width: 200px; }
          .signature-line { border-top: 1px solid #333; margin-top: 60px; padding-top: 10px; }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="company">OCB TITAN ERP</div>
          <div class="title">BUKTI HUTANG DAGANG</div>
        </div>
        <div class="info-grid">
          <div class="info-item"><div class="label">No. Hutang</div><div class="value">${ap.ap_no || '-'}</div></div>
          <div class="info-item"><div class="label">Tanggal</div><div class="value">${ap.ap_date || '-'}</div></div>
          <div class="info-item"><div class="label">Supplier</div><div class="value">${ap.supplier_name || '-'}</div></div>
          <div class="info-item"><div class="label">Jatuh Tempo</div><div class="value">${ap.due_date || '-'}</div></div>
        </div>
        <div class="amount-section">
          <div class="label">Total Hutang</div>
          <div class="amount">Rp ${(ap.original_amount || 0).toLocaleString('id-ID')}</div>
          <div style="margin-top: 10px;">
            Terbayar: Rp ${(ap.paid_amount || 0).toLocaleString('id-ID')} | 
            Outstanding: Rp ${(ap.outstanding_amount || 0).toLocaleString('id-ID')}
          </div>
        </div>
        <div class="footer">
          <div class="signature"><div>Dibuat oleh</div><div class="signature-line">${ap.created_by_name || ''}</div></div>
          <div class="signature"><div>Disetujui oleh</div><div class="signature-line">________________</div></div>
        </div>
      </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  const exportCSV = () => {
    const headers = ['No Hutang', 'Tanggal', 'Jatuh Tempo', 'Supplier', 'Invoice', 'Original', 'Outstanding', 'Status'];
    const rows = apList.map(ap => [
      ap.ap_no, ap.ap_date, ap.due_date, ap.supplier_name,
      ap.supplier_invoice_no, ap.original_amount, ap.outstanding_amount, ap.status
    ]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hutang_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const handleModalClose = (refresh = false) => {
    setShowDetail(false);
    setShowPayment(false);
    setShowEditModal(false);
    setSelectedAP(null);
    if (refresh) {
      fetchAPList();
      fetchSummary();
    }
  };

  return (
    <div className="space-y-4" data-testid="accounts-payable-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-2xl font-bold ${DESIGN.text.primary}`}>Daftar Hutang</h1>
          <p className={`text-sm ${DESIGN.text.secondary}`}>Kelola hutang ke supplier</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={exportCSV}
            variant="outline"
            className={`${DESIGN.border.default} ${DESIGN.text.primary} hover:bg-[#334155]`}
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button
            onClick={() => setShowCreateModal(true)}
            className="bg-[#F97316] hover:bg-[#EA580C] text-white"
            data-testid="btn-add-hutang"
          >
            <Plus className="w-4 h-4 mr-2" />
            Tambah Hutang
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl p-4`}>
            <div className={`text-sm ${DESIGN.text.secondary}`}>Total Hutang</div>
            <div className={`text-2xl font-bold ${DESIGN.text.primary}`}>
              {formatCurrency(summary.total_outstanding || 0)}
            </div>
          </div>
          <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl p-4`}>
            <div className={`text-sm ${DESIGN.text.secondary}`}>Jatuh Tempo</div>
            <div className="text-2xl font-bold text-rose-400">
              {formatCurrency(summary.overdue_amount || 0)}
            </div>
          </div>
          <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl p-4`}>
            <div className={`text-sm ${DESIGN.text.secondary}`}>Jumlah Hutang</div>
            <div className={`text-2xl font-bold ${DESIGN.text.accent}`}>
              {summary.total_count || 0}
            </div>
          </div>
          <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl p-4`}>
            <div className={`text-sm ${DESIGN.text.secondary}`}>Supplier Aktif</div>
            <div className={`text-2xl font-bold ${DESIGN.text.primary}`}>
              {summary.supplier_count || 0}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl p-4`}>
        <div className="flex flex-wrap gap-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${DESIGN.text.secondary}`} />
            <Input
              type="text"
              placeholder="Cari no hutang, supplier..."
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className={`pl-10 ${DESIGN.bg.input} border ${DESIGN.border.default} ${DESIGN.text.primary} placeholder:text-[#64748B]`}
              data-testid="search-hutang"
            />
          </div>
          <select
            value={supplierId}
            onChange={(e) => setSupplierId(e.target.value)}
            className={`px-3 py-2 ${DESIGN.bg.input} border ${DESIGN.border.default} ${DESIGN.text.primary} rounded-lg min-w-[180px]`}
            data-testid="filter-supplier"
          >
            <option value="">Semua Supplier</option>
            {suppliers.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className={`px-3 py-2 ${DESIGN.bg.input} border ${DESIGN.border.default} ${DESIGN.text.primary} rounded-lg min-w-[150px]`}
            data-testid="filter-status"
          >
            <option value="">Semua Status</option>
            <option value="open">Terbuka</option>
            <option value="partial">Sebagian</option>
            <option value="paid">Lunas</option>
            <option value="overdue">Jatuh Tempo</option>
            <option value="void">Void</option>
            <option value="reversed">Reversed</option>
          </select>
          <Button
            onClick={fetchAPList}
            variant="outline"
            className={`${DESIGN.border.default} ${DESIGN.text.primary}`}
          >
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl overflow-hidden`}>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className={`w-6 h-6 animate-spin ${DESIGN.text.accent}`} />
            <span className={`ml-2 ${DESIGN.text.secondary}`}>Memuat data...</span>
          </div>
        ) : apList.length === 0 ? (
          <div className="text-center py-12">
            <Wallet className={`w-12 h-12 mx-auto ${DESIGN.text.secondary} mb-4`} />
            <p className={DESIGN.text.secondary}>Belum ada data hutang</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="hutang-table">
              <thead className={DESIGN.bg.tableHeader}>
                <tr>
                  <th className={`px-4 py-3 text-left text-xs font-semibold ${DESIGN.text.secondary} uppercase tracking-wider`}>No. Hutang</th>
                  <th className={`px-4 py-3 text-left text-xs font-semibold ${DESIGN.text.secondary} uppercase tracking-wider`}>Tanggal</th>
                  <th className={`px-4 py-3 text-left text-xs font-semibold ${DESIGN.text.secondary} uppercase tracking-wider`}>Jatuh Tempo</th>
                  <th className={`px-4 py-3 text-left text-xs font-semibold ${DESIGN.text.secondary} uppercase tracking-wider`}>Supplier</th>
                  <th className={`px-4 py-3 text-right text-xs font-semibold ${DESIGN.text.secondary} uppercase tracking-wider`}>Original</th>
                  <th className={`px-4 py-3 text-right text-xs font-semibold ${DESIGN.text.secondary} uppercase tracking-wider`}>Outstanding</th>
                  <th className={`px-4 py-3 text-center text-xs font-semibold ${DESIGN.text.secondary} uppercase tracking-wider`}>Status</th>
                  <th className={`px-4 py-3 text-center text-xs font-semibold ${DESIGN.text.secondary} uppercase tracking-wider`}>Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#334155]">
                {apList.map((ap) => {
                  const statusCfg = STATUS_CONFIG[ap.status] || STATUS_CONFIG.open;
                  const overdue = isOverdue(ap.due_date) && ap.status !== 'paid';
                  
                  return (
                    <tr 
                      key={ap.id} 
                      className={`hover:bg-[#334155]/30 transition-colors ${overdue ? 'bg-rose-900/10' : ''}`}
                      data-testid={`ap-row-${ap.id}`}
                    >
                      <td className={`px-4 py-3 text-sm font-mono ${DESIGN.text.accent}`}>
                        {ap.ap_no}
                      </td>
                      <td className={`px-4 py-3 text-sm ${DESIGN.text.secondary}`}>
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(ap.ap_date)}
                        </div>
                      </td>
                      <td className={`px-4 py-3 text-sm ${overdue ? 'text-rose-400 font-medium' : DESIGN.text.secondary}`}>
                        <div className="flex items-center gap-1">
                          {overdue && <AlertTriangle className="w-3 h-3" />}
                          {formatDate(ap.due_date)}
                        </div>
                      </td>
                      <td className={`px-4 py-3 text-sm ${DESIGN.text.primary}`}>
                        <div className="flex items-center gap-1">
                          <Building2 className="w-3 h-3 text-[#9CA3AF]" />
                          {ap.supplier_name || '-'}
                        </div>
                      </td>
                      <td className={`px-4 py-3 text-sm text-right font-mono ${DESIGN.text.primary}`}>
                        {formatCurrency(ap.original_amount)}
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-mono font-medium">
                        <span className={ap.outstanding_amount > 0 ? 'text-rose-400' : 'text-emerald-400'}>
                          {formatCurrency(ap.outstanding_amount)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 ${statusCfg.bg} ${statusCfg.text} rounded-full text-xs font-medium`}>
                          {statusCfg.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-0.5">
                          {/* View Button */}
                          <button 
                            onClick={() => handleViewDetail(ap)}
                            className={`p-1.5 ${DESIGN.text.secondary} hover:bg-[#334155] rounded transition-colors`}
                            title="Lihat Detail"
                            data-testid={`btn-view-${ap.id}`}
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          
                          {/* Edit Button - Only for draft/open without payments */}
                          {ap.status !== 'paid' && (ap.paid_amount || 0) === 0 && (
                            <button 
                              onClick={() => handleEdit(ap)}
                              className="p-1.5 text-amber-400 hover:bg-amber-500/20 rounded transition-colors"
                              title="Edit"
                              data-testid={`btn-edit-${ap.id}`}
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                          )}
                          
                          {/* Pay Button */}
                          {ap.status !== 'paid' && (
                            <button 
                              onClick={() => handlePayment(ap)}
                              className="p-1.5 text-emerald-400 hover:bg-emerald-500/20 rounded transition-colors"
                              title="Bayar"
                              data-testid={`btn-pay-${ap.id}`}
                            >
                              <DollarSign className="w-4 h-4" />
                            </button>
                          )}
                          
                          {/* Print Button */}
                          <button 
                            onClick={() => handlePrint(ap)}
                            className={`p-1.5 ${DESIGN.text.secondary} hover:bg-[#334155] rounded transition-colors`}
                            title="Cetak"
                            data-testid={`btn-print-${ap.id}`}
                          >
                            <Printer className="w-4 h-4" />
                          </button>
                          
                          {/* Delete Button - Only for unpaid */}
                          {ap.status !== 'paid' && (ap.paid_amount || 0) === 0 && (
                            <button 
                              onClick={() => handleDeleteConfirm(ap)}
                              className="p-1.5 text-rose-400 hover:bg-rose-500/20 rounded transition-colors"
                              title="Hapus"
                              data-testid={`btn-delete-${ap.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && selectedAP && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className={`${DESIGN.bg.card} border ${DESIGN.border.default} rounded-xl w-full max-w-md shadow-2xl`}>
            <div className={`p-4 border-b ${DESIGN.border.default}`}>
              <h2 className={`text-lg font-semibold ${DESIGN.text.primary} flex items-center gap-2`}>
                <AlertTriangle className="h-5 w-5 text-rose-400" />
                Konfirmasi Hapus
              </h2>
            </div>
            <div className="p-4 space-y-4">
              <p className={DESIGN.text.primary}>
                Apakah Anda yakin ingin menghapus hutang ini?
              </p>
              <div className={`${DESIGN.bg.input} rounded-lg border ${DESIGN.border.default} p-3`}>
                <p className={`text-sm ${DESIGN.text.secondary}`}>No. Hutang</p>
                <p className={`${DESIGN.text.accent} font-mono`}>{selectedAP.ap_no}</p>
                <p className={`text-sm ${DESIGN.text.secondary} mt-2`}>Jumlah</p>
                <p className="text-rose-400 font-bold">{formatCurrency(selectedAP.original_amount)}</p>
              </div>
              <div className={`flex justify-end gap-3 pt-4 border-t ${DESIGN.border.default}`}>
                <Button 
                  onClick={() => { setShowDeleteConfirm(false); setSelectedAP(null); }}
                  variant="outline"
                  className={`${DESIGN.border.default} ${DESIGN.text.primary}`}
                >
                  Batal
                </Button>
                <Button 
                  onClick={handleSoftDelete}
                  disabled={actionLoading}
                  className="bg-rose-600 hover:bg-rose-700 text-white"
                  data-testid="confirm-delete"
                >
                  {actionLoading && <RefreshCw className="h-4 w-4 animate-spin mr-2" />}
                  Hapus
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetail && selectedAP && (
        <APDetailModal
          ap={selectedAP}
          onClose={handleModalClose}
        />
      )}

      {/* Payment Modal */}
      {showPayment && selectedAP && (
        <APPaymentModal
          ap={selectedAP}
          onClose={handleModalClose}
        />
      )}
    </div>
  );
}
