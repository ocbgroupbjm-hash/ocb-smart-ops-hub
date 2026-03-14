// OCB TITAN ERP - HR Leave Management Page
// Blueprint: SUPER DUPER DEWA
// Dark Theme Enterprise UI

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Calendar, Plus, Check, X, Search, RefreshCw, Download,
  Clock, Users, FileText, ChevronLeft, ChevronRight, Eye
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status Badge
const StatusBadge = ({ status }) => {
  const statusConfig = {
    pending: { label: 'Menunggu', class: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
    approved: { label: 'Disetujui', class: 'bg-green-500/20 text-green-400 border-green-500/30' },
    rejected: { label: 'Ditolak', class: 'bg-red-500/20 text-red-400 border-red-500/30' },
    cancelled: { label: 'Dibatalkan', class: 'bg-slate-500/20 text-slate-400 border-slate-500/30' }
  };
  
  const config = statusConfig[status] || statusConfig.pending;
  
  return (
    <span className={`px-2 py-1 text-xs rounded-full border ${config.class}`}>
      {config.label}
    </span>
  );
};

// Leave Request Modal
const LeaveRequestModal = ({ isOpen, onClose, employees, leaveTypes, onSubmit }) => {
  const [formData, setFormData] = useState({
    employee_id: '',
    leave_type_id: '',
    start_date: '',
    end_date: '',
    reason: '',
    notes: ''
  });
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.employee_id || !formData.leave_type_id || !formData.start_date || !formData.end_date) {
      toast.error('Lengkapi semua field wajib');
      return;
    }
    await onSubmit(formData);
    setFormData({
      employee_id: '',
      leave_type_id: '',
      start_date: '',
      end_date: '',
      reason: '',
      notes: ''
    });
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-lg">
        <div className="p-6 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-orange-500" />
            Pengajuan Cuti
          </h2>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Karyawan *</label>
            <select
              value={formData.employee_id}
              onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
              required
              data-testid="leave-employee-select"
            >
              <option value="">Pilih Karyawan</option>
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>
                  {emp.employee_id || emp.nik} - {emp.full_name || emp.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-1">Jenis Cuti *</label>
            <select
              value={formData.leave_type_id}
              onChange={(e) => setFormData({...formData, leave_type_id: e.target.value})}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
              required
              data-testid="leave-type-select"
            >
              <option value="">Pilih Jenis Cuti</option>
              {leaveTypes.map(lt => (
                <option key={lt.id} value={lt.id}>
                  {lt.name} (Max: {lt.max_days} hari)
                </option>
              ))}
            </select>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Tanggal Mulai *</label>
              <Input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                className="bg-slate-900 border-slate-700 text-white"
                required
                data-testid="leave-start-date"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Tanggal Selesai *</label>
              <Input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                className="bg-slate-900 border-slate-700 text-white"
                required
                data-testid="leave-end-date"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-1">Alasan *</label>
            <textarea
              value={formData.reason}
              onChange={(e) => setFormData({...formData, reason: e.target.value})}
              placeholder="Jelaskan alasan pengajuan cuti..."
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white min-h-[80px]"
              required
              data-testid="leave-reason-input"
            />
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-1">Catatan Tambahan</label>
            <Input
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              placeholder="Catatan tambahan (opsional)"
              className="bg-slate-900 border-slate-700 text-white"
            />
          </div>
          
          <div className="flex justify-end gap-3 pt-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={onClose}
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              Batal
            </Button>
            <Button 
              type="submit" 
              className="bg-orange-600 hover:bg-orange-700 text-white"
              data-testid="leave-submit-btn"
            >
              Ajukan Cuti
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Approval Modal
const ApprovalModal = ({ isOpen, onClose, request, onApprove }) => {
  const [status, setStatus] = useState('approved');
  const [notes, setNotes] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    await onApprove(request.id, status, notes);
    setNotes('');
  };
  
  if (!isOpen || !request) return null;
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md">
        <div className="p-6 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white">Approval Cuti</h2>
        </div>
        
        <div className="p-6">
          <div className="bg-slate-900 rounded-lg p-4 mb-4">
            <p className="text-sm text-slate-400">Karyawan</p>
            <p className="text-white font-medium">{request.employee_name}</p>
            <div className="grid grid-cols-2 gap-4 mt-3">
              <div>
                <p className="text-sm text-slate-400">Jenis Cuti</p>
                <p className="text-white">{request.leave_type_name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Durasi</p>
                <p className="text-white">{request.total_days} hari</p>
              </div>
            </div>
            <div className="mt-3">
              <p className="text-sm text-slate-400">Periode</p>
              <p className="text-white">{request.start_date} s/d {request.end_date}</p>
            </div>
            <div className="mt-3">
              <p className="text-sm text-slate-400">Alasan</p>
              <p className="text-white">{request.reason}</p>
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Keputusan</label>
              <div className="flex gap-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="status"
                    value="approved"
                    checked={status === 'approved'}
                    onChange={(e) => setStatus(e.target.value)}
                    className="accent-green-500"
                  />
                  <span className="text-green-400">Setujui</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="status"
                    value="rejected"
                    checked={status === 'rejected'}
                    onChange={(e) => setStatus(e.target.value)}
                    className="accent-red-500"
                  />
                  <span className="text-red-400">Tolak</span>
                </label>
              </div>
            </div>
            
            <div>
              <label className="block text-sm text-slate-400 mb-1">Catatan</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Catatan approval..."
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white min-h-[60px]"
              />
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
              <Button 
                type="button" 
                variant="outline" 
                onClick={onClose}
                className="border-slate-600 text-slate-300 hover:bg-slate-700"
              >
                Batal
              </Button>
              <Button 
                type="submit" 
                className={status === 'approved' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
                data-testid="approval-submit-btn"
              >
                {status === 'approved' ? (
                  <><Check className="w-4 h-4 mr-2" /> Setujui</>
                ) : (
                  <><X className="w-4 h-4 mr-2" /> Tolak</>
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Main Component
const HRLeave = () => {
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [page, setPage] = useState(1);
  
  const token = localStorage.getItem('token');
  
  const fetchLeaveRequests = useCallback(async () => {
    setLoading(true);
    try {
      let url = `${API_URL}/api/hr/leave/requests?page=${page}&limit=20`;
      if (statusFilter) url += `&status=${statusFilter}`;
      
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      
      setLeaveRequests(data.requests || []);
    } catch (error) {
      toast.error('Gagal memuat data cuti');
    }
    setLoading(false);
  }, [token, page, statusFilter]);
  
  const fetchLeaveTypes = async () => {
    try {
      const res = await fetch(`${API_URL}/api/hr/leave/types`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setLeaveTypes(data.leave_types || []);
    } catch (error) {
      console.error('Failed to fetch leave types');
    }
  };
  
  const fetchEmployees = async () => {
    try {
      const res = await fetch(`${API_URL}/api/hr/employees?status=active&limit=500`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setEmployees(data.employees || []);
    } catch (error) {
      console.error('Failed to fetch employees');
    }
  };
  
  useEffect(() => {
    fetchLeaveTypes();
    fetchEmployees();
  }, []);
  
  useEffect(() => {
    fetchLeaveRequests();
  }, [fetchLeaveRequests]);
  
  const handleSubmitRequest = async (formData) => {
    try {
      const res = await fetch(`${API_URL}/api/hr/leave/requests`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(`Pengajuan cuti berhasil: ${data.request_no}`);
        setShowRequestModal(false);
        fetchLeaveRequests();
      } else {
        toast.error(data.detail || 'Gagal mengajukan cuti');
      }
    } catch (error) {
      toast.error('Terjadi kesalahan');
    }
  };
  
  const handleApproval = async (requestId, status, notes) => {
    try {
      const res = await fetch(`${API_URL}/api/hr/leave/requests/${requestId}/approve`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status, notes })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(`Cuti ${status === 'approved' ? 'disetujui' : 'ditolak'}`);
        setShowApprovalModal(false);
        setSelectedRequest(null);
        fetchLeaveRequests();
      } else {
        toast.error(data.detail || 'Gagal proses approval');
      }
    } catch (error) {
      toast.error('Terjadi kesalahan');
    }
  };
  
  // Calculate summary stats
  const pendingCount = leaveRequests.filter(r => r.status === 'pending').length;
  const approvedCount = leaveRequests.filter(r => r.status === 'approved').length;
  const rejectedCount = leaveRequests.filter(r => r.status === 'rejected').length;
  
  return (
    <div className="min-h-screen bg-slate-900 p-6" data-testid="hr-leave-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Calendar className="w-8 h-8 text-orange-500" />
          Manajemen Cuti
        </h1>
        <p className="text-slate-400 mt-1">Leave Management System</p>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <FileText className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Total Pengajuan</p>
              <p className="text-2xl font-bold text-white">{leaveRequests.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Clock className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Menunggu Approval</p>
              <p className="text-2xl font-bold text-amber-400">{pendingCount}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <Check className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Disetujui</p>
              <p className="text-2xl font-bold text-green-400">{approvedCount}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <X className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Ditolak</p>
              <p className="text-2xl font-bold text-red-400">{rejectedCount}</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Leave Types Info */}
      {leaveTypes.length > 0 && (
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 mb-6">
          <h3 className="text-white font-medium mb-3">Jenis Cuti Tersedia</h3>
          <div className="grid grid-cols-4 gap-3">
            {leaveTypes.map(lt => (
              <div key={lt.id} className="bg-slate-900 rounded-lg p-3 border border-slate-700">
                <p className="text-white font-medium">{lt.name}</p>
                <p className="text-sm text-slate-400">Max: {lt.max_days} hari</p>
                <p className="text-xs text-slate-500 mt-1">
                  {lt.is_paid ? 'Berbayar' : 'Tidak Berbayar'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Toolbar */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button 
              onClick={() => setShowRequestModal(true)}
              className="bg-green-600 hover:bg-green-700 text-white"
              data-testid="add-leave-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              Ajukan Cuti
            </Button>
            <Button
              onClick={fetchLeaveRequests}
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
          
          <div className="flex items-center gap-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
              data-testid="status-filter"
            >
              <option value="">Semua Status</option>
              <option value="pending">Menunggu</option>
              <option value="approved">Disetujui</option>
              <option value="rejected">Ditolak</option>
            </select>
            <Button
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </div>
      
      {/* Table */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="leave-table">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">No. Request</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Karyawan</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Jenis Cuti</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Periode</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Durasi</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Alasan</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Status</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {loading ? (
                <tr>
                  <td colSpan="8" className="px-4 py-8 text-center text-slate-400">
                    Memuat data...
                  </td>
                </tr>
              ) : leaveRequests.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-4 py-8 text-center text-slate-400">
                    Tidak ada data pengajuan cuti
                  </td>
                </tr>
              ) : (
                leaveRequests.map((request) => (
                  <tr 
                    key={request.id} 
                    className="hover:bg-slate-700/30 transition-colors"
                    data-testid={`leave-row-${request.id}`}
                  >
                    <td className="px-4 py-3 text-sm text-white font-mono">
                      {request.request_no}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-white font-medium">
                        {request.employee_name}
                      </div>
                      <div className="text-xs text-slate-400">
                        {request.department_name}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {request.leave_type_name}
                    </td>
                    <td className="px-4 py-3 text-center text-sm text-slate-300">
                      <div>{request.start_date}</div>
                      <div className="text-xs text-slate-500">s/d {request.end_date}</div>
                    </td>
                    <td className="px-4 py-3 text-center text-sm text-white">
                      {request.total_days} hari
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400 max-w-[200px] truncate">
                      {request.reason}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusBadge status={request.status} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        {request.status === 'pending' && (
                          <>
                            <button
                              onClick={() => { setSelectedRequest(request); setShowApprovalModal(true); }}
                              className="p-1.5 text-green-400 hover:bg-green-500/20 rounded transition-colors"
                              title="Approve"
                              data-testid={`approve-btn-${request.id}`}
                            >
                              <Check className="w-4 h-4" />
                            </button>
                          </>
                        )}
                        <button
                          className="p-1.5 text-blue-400 hover:bg-blue-500/20 rounded transition-colors"
                          title="Detail"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Modals */}
      <LeaveRequestModal
        isOpen={showRequestModal}
        onClose={() => setShowRequestModal(false)}
        employees={employees}
        leaveTypes={leaveTypes}
        onSubmit={handleSubmitRequest}
      />
      
      <ApprovalModal
        isOpen={showApprovalModal}
        onClose={() => { setShowApprovalModal(false); setSelectedRequest(null); }}
        request={selectedRequest}
        onApprove={handleApproval}
      />
    </div>
  );
};

export default HRLeave;
