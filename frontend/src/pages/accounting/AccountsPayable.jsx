import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { 
  Search, Eye, DollarSign, AlertTriangle, RefreshCw, 
  Filter, Download, Calendar, Building2, Clock,
  TrendingUp, TrendingDown, FileText, Wallet
} from 'lucide-react';
import APDetailModal from '../../components/accounting/APDetailModal';
import APPaymentModal from '../../components/accounting/APPaymentModal';

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

  const handleModalClose = (refresh = false) => {
    setShowDetail(false);
    setShowPayment(false);
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
        <Button onClick={exportToCSV} variant="outline" data-testid="btn-export">
          <Download className="w-4 h-4 mr-2" />
          Export CSV
        </Button>
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
                          <div className="flex items-center justify-center gap-1">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleViewDetail(ap)}
                              data-testid={`btn-view-${ap.id}`}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            {ap.status !== 'paid' && (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handlePayment(ap)}
                                className="text-green-600"
                                data-testid={`btn-pay-${ap.id}`}
                              >
                                <DollarSign className="w-4 h-4" />
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
