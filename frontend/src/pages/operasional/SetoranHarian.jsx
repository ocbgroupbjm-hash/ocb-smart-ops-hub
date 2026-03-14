import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { 
  Search, Plus, Eye, CheckCircle, XCircle, FileText, 
  AlertTriangle, RefreshCw, Filter, Download, Calendar,
  Wallet, Building2, User, Clock, ArrowRight
} from 'lucide-react';
import SetoranForm from '../../components/operasional/SetoranForm';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  draft: { label: 'Draft', color: 'bg-blue-100 text-blue-800', icon: FileText },
  pending: { label: 'Menunggu Setor', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  received: { label: 'Diterima', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  verified: { label: 'Diverifikasi', color: 'bg-emerald-100 text-emerald-800', icon: CheckCircle },
  approved: { label: 'Approved', color: 'bg-teal-100 text-teal-800', icon: CheckCircle },
  posted: { label: 'Posted', color: 'bg-purple-100 text-purple-800', icon: FileText },
  rejected: { label: 'Ditolak', color: 'bg-red-100 text-red-800', icon: XCircle },
  cancelled: { label: 'Dibatalkan', color: 'bg-slate-700/50 text-slate-300', icon: XCircle }
};

const DIFF_STATUS_CONFIG = {
  match: { label: 'SESUAI', color: 'bg-green-100 text-green-800' },
  short: { label: 'KURANG', color: 'bg-red-100 text-red-800' },
  over: { label: 'LEBIH', color: 'bg-yellow-100 text-yellow-800' }
};

export default function SetoranHarian() {
  const [deposits, setDeposits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scope, setScope] = useState({});
  const [dashboard, setDashboard] = useState(null);
  
  // Filters
  const [keyword, setKeyword] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [diffFilter, setDiffFilter] = useState('');
  
  // Modal states
  const [showForm, setShowForm] = useState(false);
  const [selectedDeposit, setSelectedDeposit] = useState(null);
  const [formMode, setFormMode] = useState('create'); // create, view, edit
  
  const token = localStorage.getItem('token');

  const fetchDeposits = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (keyword) params.append('keyword', keyword);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (statusFilter) params.append('status', statusFilter);
      if (diffFilter) params.append('has_difference', diffFilter);
      
      const res = await fetch(`${API}/api/deposit/list?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      
      if (res.ok) {
        setDeposits(data.deposits || []);
        setScope(data.scope || {});
      }
    } catch (err) {
      console.error('Error fetching deposits:', err);
    } finally {
      setLoading(false);
    }
  }, [token, keyword, startDate, endDate, statusFilter, diffFilter]);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/deposit/dashboard/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDashboard(data);
      }
    } catch (err) {
      console.error('Error fetching dashboard:', err);
    }
  }, [token]);

  useEffect(() => {
    fetchDeposits();
    fetchDashboard();
  }, [fetchDeposits, fetchDashboard]);

  const handleCreateNew = () => {
    setSelectedDeposit(null);
    setFormMode('create');
    setShowForm(true);
  };

  const handleView = (deposit) => {
    setSelectedDeposit(deposit);
    setFormMode('view');
    setShowForm(true);
  };

  const handleEdit = (deposit) => {
    setSelectedDeposit(deposit);
    setFormMode('edit');
    setShowForm(true);
  };

  const handleFormClose = (refresh = false) => {
    setShowForm(false);
    setSelectedDeposit(null);
    if (refresh) {
      fetchDeposits();
      fetchDashboard();
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

  return (
    <div className="p-6 space-y-6" data-testid="setoran-harian-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Setoran Harian</h1>
          <p className="text-gray-500 text-sm mt-1">
            Kelola setoran kas harian dari kasir ke pusat
            {scope.filter_applied && (
              <span className="ml-2 text-orange-600">(Data difilter sesuai akses Anda)</span>
            )}
          </p>
        </div>
        <Button 
          onClick={handleCreateNew}
          className="bg-blue-600 hover:bg-blue-700"
          data-testid="btn-create-deposit"
        >
          <Plus className="w-4 h-4 mr-2" />
          Buat Setoran Baru
        </Button>
      </div>

      {/* Dashboard Cards */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-l-4 border-l-yellow-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Pending Setor</p>
                  <p className="text-2xl font-bold text-yellow-600">{dashboard.pending_deposit}</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Pending Verifikasi</p>
                  <p className="text-2xl font-bold text-blue-600">{dashboard.pending_verification}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-green-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Pending Approval</p>
                  <p className="text-2xl font-bold text-green-600">{dashboard.pending_approval}</p>
                </div>
                <FileText className="w-8 h-8 text-green-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-red-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Ada Selisih</p>
                  <p className="text-2xl font-bold text-red-600">{dashboard.with_difference}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-400" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Cari no setoran, kasir..."
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  className="pl-10"
                  data-testid="search-input"
                />
              </div>
            </div>
            
            <div>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                placeholder="Dari Tanggal"
                data-testid="start-date"
              />
            </div>
            
            <div>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                placeholder="Sampai Tanggal"
                data-testid="end-date"
              />
            </div>
            
            <div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full h-10 px-3 border rounded-md text-sm"
                data-testid="status-filter"
              >
                <option value="">Semua Status</option>
                <option value="draft">Draft</option>
                <option value="pending">Menunggu Setor</option>
                <option value="received">Diterima</option>
                <option value="verified">Diverifikasi</option>
                <option value="approved">Approved</option>
                <option value="posted">Posted</option>
              </select>
            </div>
            
            <div>
              <select
                value={diffFilter}
                onChange={(e) => setDiffFilter(e.target.value)}
                className="w-full h-10 px-3 border rounded-md text-sm"
                data-testid="diff-filter"
              >
                <option value="">Semua Selisih</option>
                <option value="yes">Ada Selisih</option>
                <option value="no">Tidak Ada Selisih</option>
              </select>
            </div>
          </div>
          
          <div className="flex justify-end mt-4 gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setKeyword('');
                setStartDate('');
                setEndDate('');
                setStatusFilter('');
                setDiffFilter('');
              }}
            >
              Reset
            </Button>
            <Button onClick={fetchDeposits} data-testid="btn-search">
              <Filter className="w-4 h-4 mr-2" />
              Filter
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Daftar Setoran</CardTitle>
            <Button variant="ghost" size="sm" onClick={fetchDeposits}>
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
          ) : deposits.length === 0 ? (
            <div className="text-center py-12">
              <Wallet className="w-12 h-12 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Belum ada data setoran</p>
              <Button 
                onClick={handleCreateNew} 
                className="mt-4"
                variant="outline"
              >
                Buat Setoran Pertama
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-800/50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">No. Setoran</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Tanggal</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Cabang</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Kasir</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Seharusnya</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Diterima</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Selisih</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-600">Status</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-600">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {deposits.map((dep) => {
                    const statusCfg = STATUS_CONFIG[dep.status] || STATUS_CONFIG.draft;
                    const diffCfg = DIFF_STATUS_CONFIG[dep.difference_status] || DIFF_STATUS_CONFIG.match;
                    const StatusIcon = statusCfg.icon;
                    
                    return (
                      <tr 
                        key={dep.id} 
                        className="hover:bg-slate-800/50 cursor-pointer"
                        onClick={() => handleView(dep)}
                        data-testid={`deposit-row-${dep.id}`}
                      >
                        <td className="px-4 py-3">
                          <span className="font-medium text-blue-600">{dep.deposit_number}</span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-gray-400" />
                            {formatDate(dep.deposit_date)}
                          </div>
                          <div className="text-xs text-gray-400">
                            Sales: {formatDate(dep.sales_date)}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <Building2 className="w-3 h-3 text-gray-400" />
                            {dep.branch_name || '-'}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <User className="w-3 h-3 text-gray-400" />
                            {dep.cashier_name || '-'}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right font-mono">
                          {formatCurrency(dep.cash_should_deposit)}
                        </td>
                        <td className="px-4 py-3 text-right font-mono">
                          {formatCurrency(dep.cash_received)}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <span className={`font-mono ${dep.difference_amount < 0 ? 'text-red-600' : dep.difference_amount > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
                              {formatCurrency(dep.difference_amount)}
                            </span>
                            {dep.difference_status !== 'match' && (
                              <Badge className={`${diffCfg.color} text-xs`}>
                                {diffCfg.label}
                              </Badge>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <Badge className={`${statusCfg.color} inline-flex items-center gap-1`}>
                            <StatusIcon className="w-3 h-3" />
                            {statusCfg.label}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex items-center justify-center gap-1" onClick={(e) => e.stopPropagation()}>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleView(dep)}
                              data-testid={`btn-view-${dep.id}`}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            {(dep.status === 'draft' || dep.status === 'pending') && (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleEdit(dep)}
                                data-testid={`btn-edit-${dep.id}`}
                              >
                                <ArrowRight className="w-4 h-4" />
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

      {/* Form Modal */}
      {showForm && (
        <SetoranForm
          isOpen={showForm}
          onClose={handleFormClose}
          deposit={selectedDeposit}
          mode={formMode}
        />
      )}
    </div>
  );
}
