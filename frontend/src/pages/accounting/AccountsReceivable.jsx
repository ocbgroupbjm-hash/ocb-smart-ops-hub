import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { 
  Search, Plus, Eye, DollarSign, AlertTriangle, RefreshCw, 
  Filter, Download, Calendar, User, Building2, Clock,
  TrendingUp, TrendingDown, FileText, CreditCard, XCircle
} from 'lucide-react';
import ARDetailModal from '../../components/accounting/ARDetailModal';
import ARPaymentModal from '../../components/accounting/ARPaymentModal';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  open: { label: 'Terbuka', color: 'bg-blue-100 text-blue-800' },
  partial: { label: 'Sebagian', color: 'bg-yellow-100 text-yellow-800' },
  paid: { label: 'Lunas', color: 'bg-green-100 text-green-800' },
  overdue: { label: 'Jatuh Tempo', color: 'bg-red-100 text-red-800' },
  written_off: { label: 'Dihapuskan', color: 'bg-gray-100 text-gray-800' }
};

export default function AccountsReceivable() {
  const [arList, setArList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [aging, setAging] = useState(null);
  const [customers, setCustomers] = useState([]);
  
  // Filters
  const [keyword, setKeyword] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [status, setStatus] = useState('');
  const [overdueOnly, setOverdueOnly] = useState('');
  
  // Modals
  const [selectedAR, setSelectedAR] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [showPayment, setShowPayment] = useState(false);
  
  const token = localStorage.getItem('token');

  const fetchARList = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (keyword) params.append('keyword', keyword);
      if (customerId) params.append('customer_id', customerId);
      if (status) params.append('status', status);
      if (overdueOnly) params.append('overdue_only', overdueOnly);
      
      const res = await fetch(`${API}/api/ar/list?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setArList(data.items || []);
      }
    } catch (err) {
      console.error('Error fetching AR:', err);
    } finally {
      setLoading(false);
    }
  }, [token, keyword, customerId, status, overdueOnly]);

  const fetchSummary = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ar/summary/dashboard`, {
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
      const res = await fetch(`${API}/api/ar/aging`, {
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

  const fetchCustomers = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/customers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCustomers(data.items || data || []);
      }
    } catch (err) {
      console.error('Error fetching customers:', err);
    }
  }, [token]);

  useEffect(() => {
    fetchARList();
    fetchSummary();
    fetchAging();
    fetchCustomers();
  }, [fetchARList, fetchSummary, fetchAging, fetchCustomers]);

  const handleViewDetail = (ar) => {
    setSelectedAR(ar);
    setShowDetail(true);
  };

  const handlePayment = (ar) => {
    setSelectedAR(ar);
    setShowPayment(true);
  };

  const handleModalClose = (refresh = false) => {
    setShowDetail(false);
    setShowPayment(false);
    setSelectedAR(null);
    if (refresh) {
      fetchARList();
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
    const headers = ['No AR', 'Tanggal', 'Jatuh Tempo', 'Customer', 'Original', 'Outstanding', 'Status'];
    const rows = arList.map(ar => [
      ar.ar_no,
      ar.ar_date,
      ar.due_date,
      ar.customer_name,
      ar.original_amount,
      ar.outstanding_amount,
      ar.status
    ]);
    
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `piutang_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <div className="p-6 space-y-6" data-testid="ar-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Piutang Dagang (AR)</h1>
          <p className="text-gray-500 text-sm mt-1">Kelola piutang dari penjualan kredit</p>
        </div>
        <Button onClick={exportToCSV} variant="outline" data-testid="btn-export">
          <Download className="w-4 h-4 mr-2" />
          Export CSV
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Piutang</p>
                  <p className="text-xl font-bold text-blue-600">{summary.total_ar_count}</p>
                  <p className="text-xs text-gray-400">{formatCurrency(summary.total_outstanding)}</p>
                </div>
                <CreditCard className="w-8 h-8 text-blue-400" />
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
          
          <Card className="border-l-4 border-l-green-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Outstanding</p>
                  <p className="text-lg font-bold text-green-600">{formatCurrency(summary.total_outstanding)}</p>
                </div>
                <TrendingUp className="w-8 h-8 text-green-400" />
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
              Aging Piutang
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
                  placeholder="Cari no piutang, customer..."
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  className="pl-10"
                  data-testid="search-input"
                />
              </div>
            </div>
            
            <div>
              <select
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                className="w-full h-10 px-3 border rounded-md text-sm"
                data-testid="customer-filter"
              >
                <option value="">Semua Customer</option>
                {customers.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
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
              <Button onClick={fetchARList} className="flex-1" data-testid="btn-filter">
                <Filter className="w-4 h-4 mr-1" />
                Filter
              </Button>
              <Button variant="outline" onClick={() => {
                setKeyword('');
                setCustomerId('');
                setStatus('');
                setOverdueOnly('');
              }}>
                Reset
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AR Table */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Daftar Piutang</CardTitle>
            <Button variant="ghost" size="sm" onClick={fetchARList}>
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
          ) : arList.length === 0 ? (
            <div className="text-center py-12">
              <CreditCard className="w-12 h-12 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Belum ada data piutang</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">No. Piutang</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Tanggal</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Jatuh Tempo</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Customer</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Original</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Outstanding</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-600">Status</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-600">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {arList.map((ar) => {
                    const statusCfg = STATUS_CONFIG[ar.status] || STATUS_CONFIG.open;
                    const overdue = isOverdue(ar.due_date) && ar.status !== 'paid';
                    
                    return (
                      <tr 
                        key={ar.id} 
                        className={`hover:bg-gray-50 ${overdue ? 'bg-red-50' : ''}`}
                        data-testid={`ar-row-${ar.id}`}
                      >
                        <td className="px-4 py-3">
                          <span className="font-medium text-blue-600">{ar.ar_no}</span>
                          {ar.source_no && (
                            <p className="text-xs text-gray-400">Ref: {ar.source_no}</p>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-gray-400" />
                            {formatDate(ar.ar_date)}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className={`flex items-center gap-1 ${overdue ? 'text-red-600 font-medium' : ''}`}>
                            {overdue && <AlertTriangle className="w-3 h-3" />}
                            {formatDate(ar.due_date)}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <User className="w-3 h-3 text-gray-400" />
                            {ar.customer_name || '-'}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right font-mono">
                          {formatCurrency(ar.original_amount)}
                        </td>
                        <td className="px-4 py-3 text-right font-mono font-medium">
                          <span className={ar.outstanding_amount > 0 ? 'text-red-600' : 'text-green-600'}>
                            {formatCurrency(ar.outstanding_amount)}
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
                              onClick={() => handleViewDetail(ar)}
                              data-testid={`btn-view-${ar.id}`}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            {ar.status !== 'paid' && ar.status !== 'written_off' && (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handlePayment(ar)}
                                className="text-green-600"
                                data-testid={`btn-pay-${ar.id}`}
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
      {showDetail && selectedAR && (
        <ARDetailModal
          ar={selectedAR}
          onClose={handleModalClose}
        />
      )}

      {/* Payment Modal */}
      {showPayment && selectedAR && (
        <ARPaymentModal
          ar={selectedAR}
          onClose={handleModalClose}
        />
      )}
    </div>
  );
}
