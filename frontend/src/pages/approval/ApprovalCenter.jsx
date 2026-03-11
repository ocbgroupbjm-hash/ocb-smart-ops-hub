import React, { useState, useEffect, useCallback } from 'react';
import { 
  CheckCircle2, XCircle, Clock, FileText, ChevronRight, 
  AlertCircle, Filter, Search, User, Calendar, DollarSign,
  ClipboardList, Shield, RefreshCw, Eye, MessageSquare
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Approval Status Badge
const StatusBadge = ({ status }) => {
  const styles = {
    pending: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    approved: 'bg-green-500/20 text-green-300 border-green-500/30',
    rejected: 'bg-red-500/20 text-red-300 border-red-500/30',
    cancelled: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    auto_approved: 'bg-blue-500/20 text-blue-300 border-blue-500/30'
  };
  
  const labels = {
    pending: 'Menunggu',
    approved: 'Disetujui',
    rejected: 'Ditolak',
    cancelled: 'Dibatalkan',
    auto_approved: 'Auto Approve'
  };
  
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded border ${styles[status] || styles.pending}`}>
      {labels[status] || status}
    </span>
  );
};

// Approval Type Badge
const TypeBadge = ({ type }) => {
  const styles = {
    purchase_order: 'bg-blue-500/20 text-blue-300',
    discount: 'bg-purple-500/20 text-purple-300',
    void_transaction: 'bg-red-500/20 text-red-300',
    price_override: 'bg-amber-500/20 text-amber-300',
    credit_override: 'bg-orange-500/20 text-orange-300'
  };
  
  const labels = {
    purchase_order: 'Purchase Order',
    discount: 'Diskon',
    void_transaction: 'Void Transaction',
    price_override: 'Price Override',
    credit_override: 'Credit Override'
  };
  
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded ${styles[type] || 'bg-gray-500/20 text-gray-300'}`}>
      {labels[type] || type}
    </span>
  );
};

// Detail Modal
const ApprovalDetailModal = ({ approval, onClose, onAction, isProcessing }) => {
  const [notes, setNotes] = useState('');
  
  if (!approval) return null;
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-red-900/30">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-amber-100">{approval.approval_no}</h3>
              <p className="text-sm text-gray-400 mt-1">{approval.approval_type_name}</p>
            </div>
            <StatusBadge status={approval.status} />
          </div>
        </div>
        
        <div className="p-6 space-y-4">
          {/* Reference Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500">Dokumen Referensi</label>
              <p className="text-amber-100 font-medium">{approval.reference_no}</p>
            </div>
            <div>
              <label className="text-xs text-gray-500">Tipe Referensi</label>
              <p className="text-gray-300">{approval.reference_type}</p>
            </div>
          </div>
          
          {/* Amount Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500">Nilai</label>
              <p className="text-amber-100 font-semibold text-lg">
                {approval.amount > 0 ? `Rp ${approval.amount.toLocaleString('id-ID')}` : '-'}
              </p>
            </div>
            <div>
              <label className="text-xs text-gray-500">Persentase Variance</label>
              <p className="text-amber-100 font-semibold text-lg">
                {approval.variance_percent > 0 ? `${approval.variance_percent}%` : '-'}
              </p>
            </div>
          </div>
          
          {/* Requester Info */}
          <div className="bg-red-950/20 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-red-600 to-amber-500 flex items-center justify-center text-white font-bold">
                {approval.requester_name?.[0] || 'U'}
              </div>
              <div>
                <p className="text-amber-100 font-medium">{approval.requester_name}</p>
                <p className="text-xs text-gray-400">
                  {new Date(approval.created_at).toLocaleString('id-ID')}
                </p>
              </div>
            </div>
            {approval.requester_notes && (
              <div className="mt-3 p-3 bg-black/30 rounded-lg">
                <p className="text-sm text-gray-300">{approval.requester_notes}</p>
              </div>
            )}
          </div>
          
          {/* Approval Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500">Level Diperlukan</label>
              <p className="text-amber-100">Level {approval.required_level}</p>
            </div>
            <div>
              <label className="text-xs text-gray-500">Approver Diperlukan</label>
              <div className="flex flex-wrap gap-1 mt-1">
                {approval.required_approvers?.map((role, i) => (
                  <span key={i} className="px-2 py-0.5 text-xs bg-red-900/30 text-red-200 rounded">
                    {role}
                  </span>
                ))}
              </div>
            </div>
          </div>
          
          {/* Action History */}
          {(approval.approved_by_name || approval.rejected_by_name) && (
            <div className="border-t border-red-900/30 pt-4">
              <h4 className="text-sm font-medium text-gray-400 mb-2">History Aksi</h4>
              {approval.approved_by_name && (
                <div className="flex items-center gap-2 text-green-400">
                  <CheckCircle2 className="h-4 w-4" />
                  <span className="text-sm">Disetujui oleh {approval.approved_by_name}</span>
                </div>
              )}
              {approval.rejected_by_name && (
                <div className="flex items-center gap-2 text-red-400">
                  <XCircle className="h-4 w-4" />
                  <span className="text-sm">Ditolak oleh {approval.rejected_by_name}</span>
                </div>
              )}
              {approval.action_notes && (
                <p className="mt-2 text-sm text-gray-400 italic">"{approval.action_notes}"</p>
              )}
            </div>
          )}
          
          {/* Action Form (if pending) */}
          {approval.status === 'pending' && (
            <div className="border-t border-red-900/30 pt-4">
              <label className="text-sm text-gray-400 mb-2 block">Catatan (opsional)</label>
              <textarea 
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100 placeholder-gray-500 focus:outline-none focus:border-amber-500/50"
                rows={2}
                placeholder="Tambahkan catatan..."
                data-testid="approval-notes-input"
              />
            </div>
          )}
        </div>
        
        <div className="p-6 border-t border-red-900/30 flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-amber-100 transition-colors"
            data-testid="modal-close-btn"
          >
            Tutup
          </button>
          
          {approval.status === 'pending' && (
            <>
              <button
                onClick={() => onAction(approval.id, 'reject', notes)}
                disabled={isProcessing}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors disabled:opacity-50"
                data-testid="reject-btn"
              >
                {isProcessing ? 'Memproses...' : 'Tolak'}
              </button>
              <button
                onClick={() => onAction(approval.id, 'approve', notes)}
                disabled={isProcessing}
                className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors disabled:opacity-50"
                data-testid="approve-btn"
              >
                {isProcessing ? 'Memproses...' : 'Setujui'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const ApprovalCenter = () => {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Data states
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [myRequests, setMyRequests] = useState([]);
  const [approvalTypes, setApprovalTypes] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  
  // Filter states
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Modal states
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      // Fetch all data in parallel
      const [pendingRes, myReqRes, typesRes, dashRes] = await Promise.all([
        fetch(`${API_URL}/api/approval-workflow/pending${filterType ? `?approval_type=${filterType}` : ''}`, { headers }),
        fetch(`${API_URL}/api/approval-workflow/my-requests${filterStatus ? `?status=${filterStatus}` : ''}`, { headers }),
        fetch(`${API_URL}/api/approval-workflow/types`, { headers }),
        fetch(`${API_URL}/api/approval-workflow/dashboard/summary`, { headers })
      ]);
      
      const [pendingData, myReqData, typesData, dashData] = await Promise.all([
        pendingRes.json(),
        myReqRes.json(),
        typesRes.json(),
        dashRes.json()
      ]);
      
      setPendingApprovals(pendingData.items || []);
      setMyRequests(myReqData.items || []);
      setApprovalTypes(typesData.items || []);
      setDashboardData(dashData);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token, filterType, filterStatus]);

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token, fetchData]);

  const handleAction = async (approvalId, action, notes) => {
    try {
      setIsProcessing(true);
      
      const res = await fetch(`${API_URL}/api/approval-workflow/${approvalId}/action`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action, notes })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || 'Gagal memproses approval');
      }
      
      // Refresh data
      await fetchData();
      setSelectedApproval(null);
      
    } catch (err) {
      alert(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const viewDetail = async (approvalId) => {
    try {
      const res = await fetch(`${API_URL}/api/approval-workflow/${approvalId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setSelectedApproval(data);
    } catch (err) {
      alert('Gagal memuat detail');
    }
  };

  // Filter data based on search
  const filteredPending = pendingApprovals.filter(a => 
    !searchQuery || 
    a.approval_no?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.reference_no?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.requester_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredMyRequests = myRequests.filter(a =>
    !searchQuery ||
    a.approval_no?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.reference_no?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6" data-testid="approval-center">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Approval Center</h1>
          <p className="text-gray-400 text-sm mt-1">Kelola persetujuan transaksi</p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 bg-red-900/30 hover:bg-red-900/50 text-amber-100 rounded-lg transition-colors"
          data-testid="refresh-btn"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Dashboard Summary Cards */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-yellow-900/30 to-yellow-800/10 border border-yellow-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                <Clock className="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-yellow-300">{dashboardData.total_pending || 0}</p>
                <p className="text-xs text-yellow-400/70">Total Pending</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/10 border border-blue-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Shield className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-300">{dashboardData.pending_for_my_approval || 0}</p>
                <p className="text-xs text-blue-400/70">Menunggu Approval Saya</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-green-900/30 to-green-800/10 border border-green-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                <CheckCircle2 className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-green-300">{dashboardData.today_stats?.approved || 0}</p>
                <p className="text-xs text-green-400/70">Disetujui Hari Ini</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-red-900/30 to-red-800/10 border border-red-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                <XCircle className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-red-300">{dashboardData.today_stats?.rejected || 0}</p>
                <p className="text-xs text-red-400/70">Ditolak Hari Ini</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        <button
          onClick={() => setActiveTab('pending')}
          className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'pending' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-pending"
        >
          <Clock className="h-4 w-4" />
          Pending Approvals
          {pendingApprovals.length > 0 && (
            <span className="ml-1 px-2 py-0.5 text-xs bg-yellow-500/30 text-yellow-300 rounded-full">
              {pendingApprovals.length}
            </span>
          )}
        </button>
        
        <button
          onClick={() => setActiveTab('my-requests')}
          className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'my-requests' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-my-requests"
        >
          <FileText className="h-4 w-4" />
          My Requests
        </button>
        
        <button
          onClick={() => setActiveTab('rules')}
          className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'rules' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-rules"
        >
          <ClipboardList className="h-4 w-4" />
          Approval Rules
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Cari approval..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100 placeholder-gray-500 focus:outline-none focus:border-amber-500/50"
              data-testid="search-input"
            />
          </div>
        </div>
        
        {activeTab === 'pending' && (
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100 focus:outline-none focus:border-amber-500/50"
            data-testid="filter-type"
          >
            <option value="">Semua Tipe</option>
            {approvalTypes.map(t => (
              <option key={t.code} value={t.code}>{t.name}</option>
            ))}
          </select>
        )}
        
        {activeTab === 'my-requests' && (
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100 focus:outline-none focus:border-amber-500/50"
            data-testid="filter-status"
          >
            <option value="">Semua Status</option>
            <option value="pending">Menunggu</option>
            <option value="approved">Disetujui</option>
            <option value="rejected">Ditolak</option>
          </select>
        )}
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-4 text-red-300">
          <AlertCircle className="h-5 w-5 inline mr-2" />
          {error}
        </div>
      )}

      {/* Content based on active tab */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="h-8 w-8 text-amber-500 animate-spin" />
        </div>
      ) : (
        <>
          {/* Pending Approvals Tab */}
          {activeTab === 'pending' && (
            <div className="space-y-3">
              {filteredPending.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <CheckCircle2 className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>Tidak ada approval pending</p>
                </div>
              ) : (
                filteredPending.map(approval => (
                  <div 
                    key={approval.id}
                    className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 hover:border-amber-500/30 transition-colors"
                    data-testid={`approval-item-${approval.id}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-amber-100 font-semibold">{approval.approval_no}</span>
                          <TypeBadge type={approval.approval_type} />
                          <StatusBadge status={approval.status} />
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Referensi</span>
                            <p className="text-gray-300">{approval.reference_no}</p>
                          </div>
                          <div>
                            <span className="text-gray-500">Nilai</span>
                            <p className="text-amber-100 font-medium">
                              {approval.amount > 0 
                                ? `Rp ${approval.amount.toLocaleString('id-ID')}`
                                : approval.variance_percent > 0 
                                  ? `${approval.variance_percent}%`
                                  : '-'
                              }
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-500">Pemohon</span>
                            <p className="text-gray-300">{approval.requester_name}</p>
                          </div>
                          <div>
                            <span className="text-gray-500">Tanggal</span>
                            <p className="text-gray-300">
                              {new Date(approval.created_at).toLocaleDateString('id-ID')}
                            </p>
                          </div>
                        </div>
                        
                        {approval.requester_notes && (
                          <div className="mt-3 flex items-start gap-2 text-sm">
                            <MessageSquare className="h-4 w-4 text-gray-500 mt-0.5" />
                            <p className="text-gray-400 italic">"{approval.requester_notes}"</p>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2 ml-4">
                        <button
                          onClick={() => viewDetail(approval.id)}
                          className="p-2 hover:bg-red-900/30 rounded-lg text-gray-400 hover:text-amber-100 transition-colors"
                          title="Lihat Detail"
                          data-testid={`view-detail-${approval.id}`}
                        >
                          <Eye className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleAction(approval.id, 'reject', '')}
                          className="p-2 hover:bg-red-600/30 rounded-lg text-red-400 hover:text-red-300 transition-colors"
                          title="Tolak"
                          data-testid={`quick-reject-${approval.id}`}
                        >
                          <XCircle className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleAction(approval.id, 'approve', '')}
                          className="p-2 hover:bg-green-600/30 rounded-lg text-green-400 hover:text-green-300 transition-colors"
                          title="Setujui"
                          data-testid={`quick-approve-${approval.id}`}
                        >
                          <CheckCircle2 className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* My Requests Tab */}
          {activeTab === 'my-requests' && (
            <div className="space-y-3">
              {filteredMyRequests.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>Tidak ada request</p>
                </div>
              ) : (
                filteredMyRequests.map(approval => (
                  <div 
                    key={approval.id}
                    className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 hover:border-amber-500/30 transition-colors cursor-pointer"
                    onClick={() => viewDetail(approval.id)}
                    data-testid={`my-request-${approval.id}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-amber-100 font-semibold">{approval.approval_no}</span>
                        <TypeBadge type={approval.approval_type} />
                        <StatusBadge status={approval.status} />
                      </div>
                      <ChevronRight className="h-5 w-5 text-gray-500" />
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                      <div>
                        <span className="text-gray-500">Referensi</span>
                        <p className="text-gray-300">{approval.reference_no}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Nilai</span>
                        <p className="text-amber-100">
                          {approval.amount > 0 
                            ? `Rp ${approval.amount.toLocaleString('id-ID')}`
                            : approval.variance_percent > 0 
                              ? `${approval.variance_percent}%`
                              : '-'
                          }
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-500">Tanggal</span>
                        <p className="text-gray-300">
                          {new Date(approval.created_at).toLocaleDateString('id-ID')}
                        </p>
                      </div>
                    </div>
                    
                    {approval.action_notes && (
                      <div className="mt-3 p-2 bg-black/30 rounded text-sm">
                        <span className={`font-medium ${approval.status === 'approved' ? 'text-green-400' : 'text-red-400'}`}>
                          {approval.status === 'approved' ? 'Disetujui' : 'Ditolak'}:
                        </span>
                        <span className="text-gray-400 ml-2">"{approval.action_notes}"</span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Approval Rules Tab */}
          {activeTab === 'rules' && (
            <div className="space-y-4">
              {approvalTypes.map(type => (
                <div 
                  key={type.code}
                  className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5"
                  data-testid={`rule-${type.code}`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-amber-100">{type.name}</h3>
                      <p className="text-sm text-gray-400">{type.description}</p>
                    </div>
                    <TypeBadge type={type.code} />
                  </div>
                  
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-gray-400">Level Approval:</h4>
                    <div className="grid gap-2">
                      {type.levels?.map((level, idx) => (
                        <div 
                          key={idx}
                          className="flex items-center justify-between p-3 bg-black/30 rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <span className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold ${
                              level.auto_approve 
                                ? 'bg-green-500/20 text-green-400' 
                                : 'bg-amber-500/20 text-amber-400'
                            }`}>
                              L{level.level}
                            </span>
                            <div>
                              <span className="text-gray-300">
                                {type.code.includes('discount') || type.code.includes('price') 
                                  ? `${level.min}% - ${level.max ? level.max + '%' : '∞'}`
                                  : `Rp ${level.min.toLocaleString('id-ID')} - ${level.max ? 'Rp ' + level.max.toLocaleString('id-ID') : '∞'}`
                                }
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {level.auto_approve ? (
                              <span className="px-2 py-1 text-xs bg-green-500/20 text-green-300 rounded">
                                Auto Approve
                              </span>
                            ) : (
                              level.approvers?.map((role, i) => (
                                <span key={i} className="px-2 py-1 text-xs bg-red-900/30 text-red-200 rounded">
                                  {role}
                                </span>
                              ))
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Detail Modal */}
      <ApprovalDetailModal 
        approval={selectedApproval}
        onClose={() => setSelectedApproval(null)}
        onAction={handleAction}
        isProcessing={isProcessing}
      />
    </div>
  );
};

export default ApprovalCenter;
