import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { 
  CheckCircle, XCircle, Clock, AlertTriangle, RefreshCw, 
  Filter, FileText, DollarSign, ShoppingCart, Package,
  Percent, Ban, Settings, Eye, ThumbsUp, ThumbsDown
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  approved: { label: 'Approved', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-800', icon: XCircle },
  cancelled: { label: 'Cancelled', color: 'bg-gray-100 text-gray-800', icon: Ban }
};

const MODULE_CONFIG = {
  purchase: { label: 'Pembelian', icon: ShoppingCart, color: 'text-blue-600' },
  purchase_return: { label: 'Retur Pembelian', icon: Package, color: 'text-orange-600' },
  sales_void: { label: 'Void Penjualan', icon: Ban, color: 'text-red-600' },
  sales_return: { label: 'Retur Penjualan', icon: Package, color: 'text-orange-600' },
  sales_discount: { label: 'Diskon Penjualan', icon: Percent, color: 'text-purple-600' },
  price_override: { label: 'Override Harga', icon: DollarSign, color: 'text-yellow-600' },
  stock_adjustment: { label: 'Adjustment Stok', icon: Package, color: 'text-teal-600' },
  deposit_difference: { label: 'Selisih Setoran', icon: AlertTriangle, color: 'text-red-600' },
  ar_write_off: { label: 'Write-off Piutang', icon: XCircle, color: 'text-gray-600' },
  journal_manual: { label: 'Jurnal Manual', icon: FileText, color: 'text-indigo-600' },
  expense: { label: 'Pengeluaran', icon: DollarSign, color: 'text-pink-600' }
};

export default function ApprovalCenter() {
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [allRequests, setAllRequests] = useState([]);
  const [rules, setRules] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pending');
  
  // Filters
  const [moduleFilter, setModuleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // Action modal
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [actionType, setActionType] = useState('');
  const [actionNotes, setActionNotes] = useState('');
  const [processing, setProcessing] = useState(false);
  
  const token = localStorage.getItem('token');

  const fetchPendingApprovals = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/approval/pending`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPendingApprovals(data.requests || []);
      }
    } catch (err) {
      console.error('Error fetching pending:', err);
    }
  }, [token]);

  const fetchAllRequests = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (moduleFilter) params.append('module', moduleFilter);
      if (statusFilter) params.append('status', statusFilter);
      
      const res = await fetch(`${API}/api/approval/requests?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAllRequests(data.requests || []);
      }
    } catch (err) {
      console.error('Error fetching requests:', err);
    }
  }, [token, moduleFilter, statusFilter]);

  const fetchRules = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/approval/rules`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setRules(data.rules || []);
      }
    } catch (err) {
      console.error('Error fetching rules:', err);
    }
  }, [token]);

  const fetchSummary = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/approval/summary/dashboard`, {
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

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchPendingApprovals(),
        fetchAllRequests(),
        fetchRules(),
        fetchSummary()
      ]);
      setLoading(false);
    };
    loadData();
  }, [fetchPendingApprovals, fetchAllRequests, fetchRules, fetchSummary]);

  const handleAction = async () => {
    if (!selectedRequest || !actionType) return;
    
    setProcessing(true);
    try {
      const res = await fetch(`${API}/api/approval/requests/${selectedRequest.id}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          action: actionType,
          notes: actionNotes
        })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        alert(`Request berhasil di-${actionType}`);
        setSelectedRequest(null);
        setActionType('');
        setActionNotes('');
        fetchPendingApprovals();
        fetchAllRequests();
        fetchSummary();
      } else {
        alert(data.detail || 'Gagal memproses');
      }
    } catch (err) {
      console.error('Error:', err);
      alert('Terjadi kesalahan');
    } finally {
      setProcessing(false);
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
    return new Date(dateStr).toLocaleString('id-ID', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const renderRequestCard = (req, showActions = false) => {
    const moduleInfo = MODULE_CONFIG[req.module] || { label: req.module, icon: FileText, color: 'text-gray-600' };
    const statusInfo = STATUS_CONFIG[req.status] || STATUS_CONFIG.pending;
    const ModuleIcon = moduleInfo.icon;
    const StatusIcon = statusInfo.icon;
    
    return (
      <Card key={req.id} className="hover:shadow-md transition-shadow" data-testid={`request-${req.id}`}>
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg bg-gray-100 ${moduleInfo.color}`}>
                <ModuleIcon className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium">{req.request_no}</span>
                  <Badge className={statusInfo.color}>
                    <StatusIcon className="w-3 h-3 mr-1" />
                    {statusInfo.label}
                  </Badge>
                </div>
                <p className="text-sm text-gray-500 mt-1">{moduleInfo.label}</p>
                <p className="text-sm mt-1">
                  <span className="text-gray-500">Dokumen:</span> {req.document_no}
                </p>
                <p className="text-lg font-mono font-bold text-blue-600 mt-1">
                  {formatCurrency(req.amount)}
                </p>
                {req.reason && (
                  <p className="text-sm text-gray-600 mt-1 italic">"{req.reason}"</p>
                )}
                <p className="text-xs text-gray-400 mt-2">
                  Oleh: {req.requested_by_name} | {formatDate(req.request_date)}
                </p>
                
                {/* Steps */}
                {req.steps && req.steps.length > 0 && (
                  <div className="mt-3 flex items-center gap-2">
                    {req.steps.map((step, idx) => (
                      <div 
                        key={idx}
                        className={`text-xs px-2 py-1 rounded ${
                          step.status === 'approved' ? 'bg-green-100 text-green-700' :
                          step.status === 'rejected' ? 'bg-red-100 text-red-700' :
                          step.level === req.current_level ? 'bg-yellow-100 text-yellow-700 font-medium' :
                          'bg-gray-100 text-gray-500'
                        }`}
                      >
                        L{step.level}: {step.role_code}
                        {step.status !== 'pending' && ` (${step.status})`}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            {showActions && req.status === 'pending' && (
              <div className="flex gap-2">
                <Button
                  size="sm"
                  className="bg-green-600 hover:bg-green-700"
                  onClick={() => {
                    setSelectedRequest(req);
                    setActionType('approve');
                  }}
                  data-testid={`btn-approve-${req.id}`}
                >
                  <ThumbsUp className="w-4 h-4 mr-1" />
                  Approve
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => {
                    setSelectedRequest(req);
                    setActionType('reject');
                  }}
                  data-testid={`btn-reject-${req.id}`}
                >
                  <ThumbsDown className="w-4 h-4 mr-1" />
                  Reject
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="p-6 space-y-6" data-testid="approval-center-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Approval Center</h1>
          <p className="text-gray-500 text-sm mt-1">Kelola persetujuan transaksi</p>
        </div>
        <Button variant="outline" onClick={() => {
          fetchPendingApprovals();
          fetchAllRequests();
          fetchSummary();
        }}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-l-4 border-l-yellow-500 cursor-pointer hover:shadow-md" onClick={() => setActiveTab('pending')}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Menunggu Saya</p>
                  <p className="text-2xl font-bold text-yellow-600">{summary.my_pending}</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Pending</p>
                  <p className="text-2xl font-bold text-blue-600">{summary.total_pending}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-green-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Approved</p>
                  <p className="text-2xl font-bold text-green-600">{summary.total_approved}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-red-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Rejected</p>
                  <p className="text-2xl font-bold text-red-600">{summary.total_rejected}</p>
                </div>
                <XCircle className="w-8 h-8 text-red-400" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b">
        {[
          { key: 'pending', label: 'Pending Approval', count: pendingApprovals.length },
          { key: 'all', label: 'Semua Request', count: allRequests.length },
          { key: 'rules', label: 'Approval Rules', count: rules.length }
        ].map(tab => (
          <button
            key={tab.key}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab(tab.key)}
            data-testid={`tab-${tab.key}`}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
          <span className="ml-2 text-gray-500">Memuat data...</span>
        </div>
      ) : (
        <>
          {/* Pending Tab */}
          {activeTab === 'pending' && (
            <div className="space-y-4">
              {pendingApprovals.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle className="w-12 h-12 mx-auto text-green-300 mb-4" />
                  <p className="text-gray-500">Tidak ada approval yang menunggu</p>
                </div>
              ) : (
                pendingApprovals.map(req => renderRequestCard(req, true))
              )}
            </div>
          )}

          {/* All Requests Tab */}
          {activeTab === 'all' && (
            <>
              {/* Filters */}
              <Card className="mb-4">
                <CardContent className="p-4">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <select
                      value={moduleFilter}
                      onChange={(e) => setModuleFilter(e.target.value)}
                      className="h-10 px-3 border rounded-md text-sm"
                    >
                      <option value="">Semua Module</option>
                      {Object.entries(MODULE_CONFIG).map(([key, val]) => (
                        <option key={key} value={key}>{val.label}</option>
                      ))}
                    </select>
                    
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="h-10 px-3 border rounded-md text-sm"
                    >
                      <option value="">Semua Status</option>
                      <option value="pending">Pending</option>
                      <option value="approved">Approved</option>
                      <option value="rejected">Rejected</option>
                    </select>
                    
                    <Button onClick={fetchAllRequests}>
                      <Filter className="w-4 h-4 mr-2" />
                      Filter
                    </Button>
                  </div>
                </CardContent>
              </Card>
              
              <div className="space-y-4">
                {allRequests.length === 0 ? (
                  <div className="text-center py-12">
                    <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                    <p className="text-gray-500">Tidak ada request</p>
                  </div>
                ) : (
                  allRequests.map(req => renderRequestCard(req, false))
                )}
              </div>
            </>
          )}

          {/* Rules Tab */}
          {activeTab === 'rules' && (
            <div className="space-y-4">
              {rules.length === 0 ? (
                <div className="text-center py-12">
                  <Settings className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">Belum ada approval rules</p>
                </div>
              ) : (
                rules.map(rule => {
                  const moduleInfo = MODULE_CONFIG[rule.module] || { label: rule.module, icon: FileText };
                  const ModuleIcon = moduleInfo.icon;
                  
                  return (
                    <Card key={rule.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <div className="p-2 rounded-lg bg-gray-100">
                              <ModuleIcon className="w-5 h-5 text-gray-600" />
                            </div>
                            <div>
                              <p className="font-medium">{rule.rule_name}</p>
                              <p className="text-sm text-gray-500">{moduleInfo.label}</p>
                              <p className="text-sm mt-1">
                                <span className="font-mono bg-gray-100 px-2 py-1 rounded">
                                  {rule.condition_type} {rule.condition_operator} {rule.condition_value.toLocaleString()}
                                </span>
                              </p>
                              <div className="flex gap-2 mt-2">
                                {rule.approval_levels?.map((level, idx) => (
                                  <Badge key={idx} variant="outline">
                                    L{level.level}: {level.role_code}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </div>
                          <Badge className={rule.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                            {rule.active ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          )}
        </>
      )}

      {/* Action Modal */}
      {selectedRequest && actionType && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-md p-6">
            <h3 className="text-lg font-bold mb-4">
              {actionType === 'approve' ? 'Approve Request' : 'Reject Request'}
            </h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-500">Request</p>
                <p className="font-medium">{selectedRequest.request_no}</p>
                <p className="text-sm">{selectedRequest.document_no}</p>
                <p className="font-mono font-bold text-blue-600">{formatCurrency(selectedRequest.amount)}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">
                  Catatan {actionType === 'reject' && <span className="text-red-500">*</span>}
                </label>
                <Textarea
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  placeholder={actionType === 'reject' ? 'Alasan penolakan...' : 'Catatan (opsional)'}
                  rows={3}
                />
              </div>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <Button variant="outline" onClick={() => {
                setSelectedRequest(null);
                setActionType('');
                setActionNotes('');
              }}>
                Batal
              </Button>
              <Button
                onClick={handleAction}
                disabled={processing || (actionType === 'reject' && !actionNotes.trim())}
                className={actionType === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
              >
                {processing ? (
                  <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                ) : actionType === 'approve' ? (
                  <ThumbsUp className="w-4 h-4 mr-2" />
                ) : (
                  <ThumbsDown className="w-4 h-4 mr-2" />
                )}
                {actionType === 'approve' ? 'Approve' : 'Reject'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
