import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { 
  Search, Eye, DollarSign, AlertTriangle, RefreshCw, 
  Filter, Download, Calendar, Building2, Clock,
  TrendingUp, TrendingDown, FileText, Wallet, Edit, Trash2, Printer, Plus
} from 'lucide-react';
import APDetailModal from '../../components/accounting/APDetailModal';
import APPaymentModal from '../../components/accounting/APPaymentModal';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  open: { label: 'Terbuka', color: 'bg-blue-100 text-blue-800' },
  partial: { label: 'Sebagian', color: 'bg-yellow-100 text-yellow-800' },
  paid: { label: 'Lunas', color: 'bg-green-100 text-green-800' },
  overdue: { label: 'Jatuh Tempo', color: 'bg-red-100 text-red-800' }
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
    // Only allow edit for draft/open status that hasn't been paid yet
    if (ap.status === 'paid') {
      toast.error('Hutang lunas tidak bisa diedit. Gunakan jurnal koreksi.');
      return;
    }
    if (ap.paid_amount > 0) {
      toast.error('Hutang yang sudah ada pembayaran tidak bisa diedit langsung. Gunakan jurnal koreksi.');
      return;
    }
    setSelectedAP(ap);
    setShowEditModal(true);
  };

  const handleSoftDelete = async (ap) => {
    // Validation: cannot delete if has payments or journal
    if (ap.status === 'paid' || ap.paid_amount > 0) {
      toast.error('Tidak dapat menghapus hutang yang sudah ada pembayaran');
      return;
    }
    
    if (!window.confirm(`Yakin ingin menghapus hutang ${ap.ap_no}? Data akan di-soft delete.`)) {
      return;
    }

    try {
      const res = await fetch(`${API}/api/ap/${ap.id}/soft-delete`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        toast.success('Hutang berhasil dihapus');
        fetchAPList();
        fetchSummary();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Gagal menghapus hutang');
      }
    } catch (err) {
      console.error('Delete error:', err);
      toast.error('Terjadi kesalahan saat menghapus');
    }
  };

  const handlePrint = (ap) => {
    // Open print modal or generate PDF
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
          @media print { body { padding: 0; } }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="company">OCB TITAN ERP</div>
          <div class="title">BUKTI HUTANG DAGANG</div>
        </div>
        
        <div class="info-grid">
          <div class="info-item">
            <div class="label">No. Hutang</div>
            <div class="value">${ap.ap_no || '-'}</div>
          </div>
          <div class="info-item">
            <div class="label">Tanggal</div>
            <div class="value">${ap.ap_date || '-'}</div>
          </div>
          <div class="info-item">
            <div class="label">Supplier</div>
            <div class="value">${ap.supplier_name || '-'}</div>
          </div>
          <div class="info-item">
            <div class="label">Jatuh Tempo</div>
            <div class="value">${ap.due_date || '-'}</div>
          </div>
          <div class="info-item">
            <div class="label">No. Invoice Supplier</div>
            <div class="value">${ap.supplier_invoice_no || '-'}</div>
          </div>
          <div class="info-item">
            <div class="label">Status</div>
            <div class="value">${ap.status?.toUpperCase() || 'OPEN'}</div>
          </div>
        </div>
        
        <div class="amount-section">
          <div class="label">Total Hutang</div>
          <div class="amount">Rp ${(ap.original_amount || 0).toLocaleString('id-ID')}</div>
          <div style="margin-top: 10px;">
            <span>Terbayar: Rp ${(ap.paid_amount || 0).toLocaleString('id-ID')}</span>
            <span style="margin-left: 20px;">Outstanding: Rp ${(ap.outstanding_amount || 0).toLocaleString('id-ID')}</span>
          </div>
        </div>
        
        ${ap.notes ? `<div style="margin: 20px 0;"><strong>Catatan:</strong> ${ap.notes}</div>` : ''}
        
        <div class="footer">
          <div class="signature">
            <div>Dibuat oleh</div>
            <div class="signature-line">${ap.created_by_name || ''}</div>
          </div>
          <div class="signature">
            <div>Disetujui oleh</div>
            <div class="signature-line">________________</div>
          </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px; font-size: 11px; color: #666;">
          Dicetak pada: ${new Date().toLocaleString('id-ID')}
        </div>
        
        <script>window.onload = function() { window.print(); }</script>
      </body>
      </html>
    `);
    printWindow.document.close();
  };

  const handleModalClose = (refresh = false) => {
    setShowDetail(false);
    setShowPayment(false);
    setShowCreateModal(false);
    setShowEditModal(false);
    setSelectedAP(null);
    if (refresh) {
      fetchAPList();
      fetchSummary();
      fetchAging();
    }
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('id-ID', { 
      style: 'currency', 
      currency: 'IDR',
      minimumFractionDigits: 0 
    }).format(val || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('id-ID', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  const isOverdue = (dueDate) => {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date();
  };

  const exportToCSV = () => {
    const headers = ['No AP', 'Tanggal', 'Jatuh Tempo', 'Supplier', 'Invoice', 'Original', 'Outstanding', 'Status'];
    const rows = apList.map(ap => [
      ap.ap_no,
      ap.ap_date,
      ap.due_date,
      ap.supplier_name,
      ap.supplier_invoice_no,
      ap.original_amount,
      ap.outstanding_amount,
      ap.status
    ]);
    
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hutang_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <div className="p-6 space-y-6" data-testid="ap-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Hutang Dagang (AP)</h1>
          <p className="text-gray-500 text-sm mt-1">Kelola hutang ke supplier</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowCreateModal(true)} className="bg-purple-600 hover:bg-purple-700" data-testid="btn-add-ap">
            <Plus className="w-4 h-4 mr-2" />
            Tambah Hutang
          </Button>
          <Button onClick={exportToCSV} variant="outline" data-testid="btn-export">
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-l-4 border-l-purple-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Hutang</p>
                  <p className="text-xl font-bold text-purple-600">{summary.total_ap_count}</p>
                  <p className="text-xs text-gray-400">{formatCurrency(summary.total_outstanding)}</p>
                </div>
                <Wallet className="w-8 h-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-red-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Jatuh Tempo</p>
                  <p className="text-xl font-bold text-red-600">{summary.overdue_count}</p>
                  <p className="text-xs text-gray-400">{formatCurrency(summary.overdue_amount)}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-yellow-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Jatuh Tempo 7 Hari</p>
                  <p className="text-xl font-bold text-yellow-600">{summary.due_this_week}</p>
                  <p className="text-xs text-gray-400">{formatCurrency(summary.due_this_week_amount)}</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-orange-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Outstanding</p>
                  <p className="text-lg font-bold text-orange-600">{formatCurrency(summary.total_outstanding)}</p>
                </div>
                <TrendingDown className="w-8 h-8 text-orange-400" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Aging Report */}
      {aging && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingDown className="w-5 h-5" />
              Aging Hutang
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-4">
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">Current</p>
                <p className="font-bold text-green-700">{aging.current?.count || 0}</p>
                <p className="text-xs text-green-600">{formatCurrency(aging.current?.amount || 0)}</p>
              </div>
              <div className="text-center p-3 bg-yellow-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">1-30 Hari</p>
                <p className="font-bold text-yellow-700">{aging['1_30']?.count || 0}</p>
                <p className="text-xs text-yellow-600">{formatCurrency(aging['1_30']?.amount || 0)}</p>
              </div>
              <div className="text-center p-3 bg-orange-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">31-60 Hari</p>
                <p className="font-bold text-orange-700">{aging['31_60']?.count || 0}</p>
                <p className="text-xs text-orange-600">{formatCurrency(aging['31_60']?.amount || 0)}</p>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">61-90 Hari</p>
                <p className="font-bold text-red-700">{aging['61_90']?.count || 0}</p>
                <p className="text-xs text-red-600">{formatCurrency(aging['61_90']?.amount || 0)}</p>
              </div>
              <div className="text-center p-3 bg-gray-100 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">&gt;90 Hari</p>
                <p className="font-bold text-gray-700">{aging.over_90?.count || 0}</p>
                <p className="text-xs text-gray-600">{formatCurrency(aging.over_90?.amount || 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Cari no hutang, supplier..."
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  className="pl-10"
                  data-testid="search-input"
                />
              </div>
            </div>
            
            <div>
              <select
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
                className="w-full h-10 px-3 border rounded-md text-sm"
                data-testid="supplier-filter"
              >
                <option value="">Semua Supplier</option>
                {suppliers.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full h-10 px-3 border rounded-md text-sm"
                data-testid="status-filter"
              >
                <option value="">Semua Status</option>
                <option value="open">Terbuka</option>
                <option value="partial">Sebagian</option>
                <option value="paid">Lunas</option>
                <option value="overdue">Jatuh Tempo</option>
              </select>
            </div>
            
            <div className="flex gap-2">
              <Button onClick={fetchAPList} className="flex-1" data-testid="btn-filter">
                <Filter className="w-4 h-4 mr-1" />
                Filter
              </Button>
              <Button variant="outline" onClick={() => {
                setKeyword('');
                setSupplierId('');
                setStatus('');
              }}>
                Reset
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AP Table */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Daftar Hutang</CardTitle>
            <Button variant="ghost" size="sm" onClick={fetchAPList}>
              <RefreshCw className="w-4 h-4 mr-1" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">Memuat data...</span>
            </div>
          ) : apList.length === 0 ? (
            <div className="text-center py-12">
              <Wallet className="w-12 h-12 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Belum ada data hutang</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">No. Hutang</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Tanggal</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Jatuh Tempo</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Supplier</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Invoice</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Original</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Outstanding</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-600">Status</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-600">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {apList.map((ap) => {
                    const statusCfg = STATUS_CONFIG[ap.status] || STATUS_CONFIG.open;
                    const overdue = isOverdue(ap.due_date) && ap.status !== 'paid';
                    
                    return (
                      <tr 
                        key={ap.id} 
                        className={`hover:bg-gray-50 ${overdue ? 'bg-red-50' : ''}`}
                        data-testid={`ap-row-${ap.id}`}
                      >
                        <td className="px-4 py-3">
                          <span className="font-medium text-purple-600">{ap.ap_no}</span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-gray-400" />
                            {formatDate(ap.ap_date)}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className={`flex items-center gap-1 ${overdue ? 'text-red-600 font-medium' : ''}`}>
                            {overdue && <AlertTriangle className="w-3 h-3" />}
                            {formatDate(ap.due_date)}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <Building2 className="w-3 h-3 text-gray-400" />
                            {ap.supplier_name || '-'}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="font-mono text-xs">{ap.supplier_invoice_no || '-'}</span>
                        </td>
                        <td className="px-4 py-3 text-right font-mono">
                          {formatCurrency(ap.original_amount)}
                        </td>
                        <td className="px-4 py-3 text-right font-mono font-medium">
                          <span className={ap.outstanding_amount > 0 ? 'text-red-600' : 'text-green-600'}>
                            {formatCurrency(ap.outstanding_amount)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <Badge className={statusCfg.color}>
                            {statusCfg.label}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex items-center justify-center gap-0.5">
                            {/* Detail Button */}
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleViewDetail(ap)}
                              title="Lihat Detail"
                              data-testid={`btn-view-${ap.id}`}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            
                            {/* Edit Button - Only for draft/open without payments */}
                            {ap.status !== 'paid' && (ap.paid_amount || 0) === 0 && (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleEdit(ap)}
                                title="Edit"
                                className="text-blue-600"
                                data-testid={`btn-edit-${ap.id}`}
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                            )}
                            
                            {/* Pay Button */}
                            {ap.status !== 'paid' && (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handlePayment(ap)}
                                title="Bayar"
                                className="text-green-600"
                                data-testid={`btn-pay-${ap.id}`}
                              >
                                <DollarSign className="w-4 h-4" />
                              </Button>
                            )}
                            
                            {/* Print Button */}
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handlePrint(ap)}
                              title="Cetak"
                              className="text-gray-600"
                              data-testid={`btn-print-${ap.id}`}
                            >
                              <Printer className="w-4 h-4" />
                            </Button>
                            
                            {/* Delete Button - Soft delete only for unpaid */}
                            {ap.status !== 'paid' && (ap.paid_amount || 0) === 0 && (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleSoftDelete(ap)}
                                title="Hapus"
                                className="text-red-600"
                                data-testid={`btn-delete-${ap.id}`}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
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
        </CardContent>
      </Card>

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
