// OCB TITAN ERP - HR Employee Management Page
// Blueprint: SUPER DUPER DEWA
// Dark Theme Enterprise UI

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Users, Plus, Edit2, Trash2, Search, Filter, Download,
  Building2, Briefcase, Mail, Phone, Calendar, DollarSign,
  UserCheck, UserX, ChevronLeft, ChevronRight, Eye, RefreshCw,
  Upload, FileText, Image, X
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status badge component
const StatusBadge = ({ status }) => {
  const statusConfig = {
    active: { label: 'Aktif', class: 'bg-green-500/20 text-green-400 border-green-500/30' },
    inactive: { label: 'Non-Aktif', class: 'bg-slate-500/20 text-slate-400 border-slate-500/30' },
    resigned: { label: 'Resign', class: 'bg-red-500/20 text-red-400 border-red-500/30' },
    terminated: { label: 'Terminated', class: 'bg-red-600/20 text-red-500 border-red-600/30' },
    probation: { label: 'Probation', class: 'bg-amber-500/20 text-amber-400 border-amber-500/30' }
  };
  
  const config = statusConfig[status] || statusConfig.active;
  
  return (
    <span className={`px-2 py-1 text-xs rounded-full border ${config.class}`}>
      {config.label}
    </span>
  );
};

// Document Upload Component
const DocumentUploadSection = ({ employeeId, token, onRefresh }) => {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [selectedType, setSelectedType] = useState('ktp');
  const fileInputRef = useRef(null);
  
  const documentTypes = [
    { code: 'ktp', name: 'KTP' },
    { code: 'npwp', name: 'NPWP' },
    { code: 'contract', name: 'Kontrak Kerja' },
    { code: 'photo', name: 'Foto' },
    { code: 'other', name: 'Lainnya' }
  ];
  
  const fetchDocuments = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/hr/employees/${employeeId}/documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  }, [employeeId, token]);
  
  useEffect(() => {
    if (employeeId) {
      fetchDocuments();
    }
  }, [employeeId, fetchDocuments]);
  
  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Ukuran file melebihi 5MB');
      return;
    }
    
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Format file tidak didukung. Gunakan JPG, PNG, atau PDF');
      return;
    }
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await fetch(
        `${API_URL}/api/hr/employees/${employeeId}/documents?document_type=${selectedType}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: formData
        }
      );
      
      if (res.ok) {
        toast.success('Dokumen berhasil diupload');
        fetchDocuments();
        if (onRefresh) onRefresh();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Gagal upload dokumen');
      }
    } catch (error) {
      toast.error('Error uploading document');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };
  
  const handleDelete = async (documentId) => {
    if (!window.confirm('Hapus dokumen ini?')) return;
    
    try {
      const res = await fetch(
        `${API_URL}/api/hr/employees/${employeeId}/documents/${documentId}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      if (res.ok) {
        toast.success('Dokumen dihapus');
        fetchDocuments();
      }
    } catch (error) {
      toast.error('Error deleting document');
    }
  };
  
  const getDocIcon = (type) => {
    if (type === 'photo') return <Image className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };
  
  return (
    <div className="mt-4 pt-4 border-t border-slate-700">
      <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
        <FileText className="w-4 h-4 text-orange-500" />
        Dokumen Karyawan
      </h3>
      
      {/* Upload Form */}
      <div className="flex gap-2 mb-3">
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-white"
          data-testid="document-type-select"
        >
          {documentTypes.map(t => (
            <option key={t.code} value={t.code}>{t.name}</option>
          ))}
        </select>
        <input
          ref={fileInputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.pdf"
          onChange={handleUpload}
          className="hidden"
          data-testid="document-file-input"
        />
        <Button
          size="sm"
          variant="outline"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="border-orange-500 text-orange-400 hover:bg-orange-500/10"
          data-testid="upload-document-btn"
        >
          <Upload className="w-4 h-4 mr-1" />
          {uploading ? 'Uploading...' : 'Upload'}
        </Button>
      </div>
      
      {/* Document List */}
      {documents.length > 0 ? (
        <div className="space-y-2">
          {documents.map(doc => (
            <div key={doc.id} className="flex items-center justify-between bg-slate-900 rounded px-3 py-2">
              <div className="flex items-center gap-2">
                {getDocIcon(doc.type)}
                <div>
                  <p className="text-sm text-white">{doc.type.toUpperCase()}</p>
                  <p className="text-xs text-slate-400">{doc.original_filename}</p>
                </div>
              </div>
              <button
                onClick={() => handleDelete(doc.id)}
                className="text-slate-400 hover:text-red-400"
                data-testid={`delete-doc-${doc.id}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-slate-500">Belum ada dokumen</p>
      )}
    </div>
  );
};

// Employee Modal Component
const EmployeeModal = ({ isOpen, onClose, employee, departments, positions, onSave }) => {
  const [formData, setFormData] = useState({
    employee_id: '',
    full_name: '',
    email: '',
    phone: '',
    department_id: '',
    position_id: '',
    employment_type: 'permanent',
    join_date: new Date().toISOString().split('T')[0],
    salary_base: 0,
    bank_name: '',
    bank_account: '',
    gender: 'male',
    marital_status: 'single'
  });
  
  useEffect(() => {
    if (employee) {
      setFormData({
        employee_id: employee.employee_id || employee.nik || '',
        full_name: employee.full_name || employee.name || '',
        email: employee.email || '',
        phone: employee.phone || '',
        department_id: employee.department_id || '',
        position_id: employee.position_id || employee.jabatan_id || '',
        employment_type: employee.employment_type || 'permanent',
        join_date: employee.join_date || new Date().toISOString().split('T')[0],
        salary_base: employee.salary_base || 0,
        bank_name: employee.bank_name || '',
        bank_account: employee.bank_account || '',
        gender: employee.gender || 'male',
        marital_status: employee.marital_status || 'single'
      });
    } else {
      setFormData({
        employee_id: '',
        full_name: '',
        email: '',
        phone: '',
        department_id: '',
        position_id: '',
        employment_type: 'permanent',
        join_date: new Date().toISOString().split('T')[0],
        salary_base: 0,
        bank_name: '',
        bank_account: '',
        gender: 'male',
        marital_status: 'single'
      });
    }
  }, [employee]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    await onSave(formData, !!employee);
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-orange-500" />
            {employee ? 'Edit Karyawan' : 'Tambah Karyawan Baru'}
          </h2>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">NIK Karyawan *</label>
              <Input
                value={formData.employee_id}
                onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
                placeholder="EMP-001"
                className="bg-slate-900 border-slate-700 text-white"
                required
                disabled={!!employee}
                data-testid="employee-nik-input"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Nama Lengkap *</label>
              <Input
                value={formData.full_name}
                onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                placeholder="Ahmad Suhendra"
                className="bg-slate-900 border-slate-700 text-white"
                required
                data-testid="employee-name-input"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Email</label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="email@company.com"
                className="bg-slate-900 border-slate-700 text-white"
                data-testid="employee-email-input"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">No. Telepon</label>
              <Input
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                placeholder="081234567890"
                className="bg-slate-900 border-slate-700 text-white"
                data-testid="employee-phone-input"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Departemen *</label>
              <select
                value={formData.department_id}
                onChange={(e) => setFormData({...formData, department_id: e.target.value})}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
                required
                data-testid="employee-department-select"
              >
                <option value="">Pilih Departemen</option>
                {departments.map(d => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Posisi/Jabatan *</label>
              <select
                value={formData.position_id}
                onChange={(e) => setFormData({...formData, position_id: e.target.value})}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
                required
                data-testid="employee-position-select"
              >
                <option value="">Pilih Posisi</option>
                {positions.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Tipe Kepegawaian</label>
              <select
                value={formData.employment_type}
                onChange={(e) => setFormData({...formData, employment_type: e.target.value})}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
                data-testid="employee-type-select"
              >
                <option value="permanent">Tetap</option>
                <option value="contract">Kontrak</option>
                <option value="probation">Probation</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Tanggal Bergabung *</label>
              <Input
                type="date"
                value={formData.join_date}
                onChange={(e) => setFormData({...formData, join_date: e.target.value})}
                className="bg-slate-900 border-slate-700 text-white"
                required
                data-testid="employee-joindate-input"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Gaji Pokok</label>
              <Input
                type="number"
                value={formData.salary_base}
                onChange={(e) => setFormData({...formData, salary_base: parseFloat(e.target.value) || 0})}
                placeholder="5000000"
                className="bg-slate-900 border-slate-700 text-white"
                data-testid="employee-salary-input"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Nama Bank</label>
              <Input
                value={formData.bank_name}
                onChange={(e) => setFormData({...formData, bank_name: e.target.value})}
                placeholder="BCA"
                className="bg-slate-900 border-slate-700 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">No. Rekening</label>
              <Input
                value={formData.bank_account}
                onChange={(e) => setFormData({...formData, bank_account: e.target.value})}
                placeholder="1234567890"
                className="bg-slate-900 border-slate-700 text-white"
              />
            </div>
          </div>
          
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
            <Button 
              type="button" 
              variant="outline" 
              onClick={onClose}
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              data-testid="employee-modal-cancel"
            >
              Batal
            </Button>
            <Button 
              type="submit" 
              className="bg-orange-600 hover:bg-orange-700 text-white"
              data-testid="employee-modal-save"
            >
              {employee ? 'Update' : 'Simpan'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main Component
const HREmployees = () => {
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [detailEmployee, setDetailEmployee] = useState(null);
  
  const token = localStorage.getItem('token');
  
  const fetchEmployees = useCallback(async () => {
    setLoading(true);
    try {
      let url = `${API_URL}/api/hr/employees?page=${page}&limit=20`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      if (deptFilter) url += `&department_id=${deptFilter}`;
      
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      
      setEmployees(data.employees || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      toast.error('Gagal memuat data karyawan');
    }
    setLoading(false);
  }, [token, page, search, statusFilter, deptFilter]);
  
  const fetchDepartments = async () => {
    try {
      const res = await fetch(`${API_URL}/api/hr/departments`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setDepartments(data.departments || []);
    } catch (error) {
      console.error('Failed to fetch departments');
    }
  };
  
  const fetchPositions = async () => {
    try {
      const res = await fetch(`${API_URL}/api/hr/positions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setPositions(data.positions || []);
    } catch (error) {
      console.error('Failed to fetch positions');
    }
  };
  
  useEffect(() => {
    fetchDepartments();
    fetchPositions();
  }, []);
  
  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);
  
  const handleSaveEmployee = async (formData, isEdit) => {
    try {
      const url = isEdit 
        ? `${API_URL}/api/hr/employees/${selectedEmployee.id}`
        : `${API_URL}/api/hr/employees`;
      
      const res = await fetch(url, {
        method: isEdit ? 'PUT' : 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(isEdit ? 'Karyawan berhasil diupdate' : 'Karyawan berhasil ditambahkan');
        setShowModal(false);
        setSelectedEmployee(null);
        fetchEmployees();
      } else {
        toast.error(data.detail || 'Gagal menyimpan data');
      }
    } catch (error) {
      toast.error('Terjadi kesalahan');
    }
  };
  
  const handleDelete = async (employee) => {
    if (!window.confirm(`Yakin ingin menonaktifkan karyawan ${employee.full_name || employee.name}?`)) return;
    
    try {
      const res = await fetch(`${API_URL}/api/hr/employees/${employee.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        toast.success('Karyawan berhasil dinonaktifkan');
        fetchEmployees();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Gagal menonaktifkan karyawan');
      }
    } catch (error) {
      toast.error('Terjadi kesalahan');
    }
  };
  
  const handleViewDetail = (employee) => {
    setDetailEmployee(employee);
    setShowDetail(true);
  };
  
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
  };
  
  return (
    <div className="min-h-screen bg-slate-900 p-6" data-testid="hr-employees-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Users className="w-8 h-8 text-orange-500" />
          Manajemen Karyawan
        </h1>
        <p className="text-slate-400 mt-1">Employee Master - Single Source of Truth</p>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Users className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Total Karyawan</p>
              <p className="text-xl font-bold text-white">{total}</p>
            </div>
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <UserCheck className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Aktif</p>
              <p className="text-xl font-bold text-white">
                {employees.filter(e => e.status === 'active' || !e.status).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Building2 className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Departemen</p>
              <p className="text-xl font-bold text-white">{departments.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Briefcase className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Posisi</p>
              <p className="text-xl font-bold text-white">{positions.length}</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Toolbar */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button 
              onClick={() => { setSelectedEmployee(null); setShowModal(true); }}
              className="bg-green-600 hover:bg-green-700 text-white"
              data-testid="add-employee-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              Tambah Karyawan
            </Button>
            <Button
              onClick={fetchEmployees}
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              data-testid="refresh-btn"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              data-testid="export-btn"
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Cari karyawan..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 bg-slate-900 border-slate-700 text-white w-64"
                data-testid="search-input"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
              data-testid="status-filter"
            >
              <option value="">Semua Status</option>
              <option value="active">Aktif</option>
              <option value="inactive">Non-Aktif</option>
              <option value="resigned">Resign</option>
            </select>
            <select
              value={deptFilter}
              onChange={(e) => setDeptFilter(e.target.value)}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
              data-testid="department-filter"
            >
              <option value="">Semua Departemen</option>
              {departments.map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
      
      {/* Table */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="employee-table">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">NIK</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Nama</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Departemen</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Posisi</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Email</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Telepon</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-slate-300">Gaji</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Status</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {loading ? (
                <tr>
                  <td colSpan="9" className="px-4 py-8 text-center text-slate-400">
                    Memuat data...
                  </td>
                </tr>
              ) : employees.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-4 py-8 text-center text-slate-400">
                    Tidak ada data karyawan
                  </td>
                </tr>
              ) : (
                employees.map((emp) => (
                  <tr 
                    key={emp.id} 
                    className="hover:bg-slate-700/30 transition-colors"
                    data-testid={`employee-row-${emp.id}`}
                  >
                    <td className="px-4 py-3 text-sm text-white font-mono">
                      {emp.employee_id || emp.nik || '-'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-white font-medium">
                        {emp.full_name || emp.name}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {emp.department_name || emp.department || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {emp.position_name || emp.jabatan_name || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {emp.email || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {emp.phone || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-green-400">
                      {formatCurrency(emp.salary_base)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusBadge status={emp.status || 'active'} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => handleViewDetail(emp)}
                          className="p-1.5 text-blue-400 hover:bg-blue-500/20 rounded transition-colors"
                          title="Lihat Detail"
                          data-testid={`view-btn-${emp.id}`}
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => { setSelectedEmployee(emp); setShowModal(true); }}
                          className="p-1.5 text-purple-400 hover:bg-purple-500/20 rounded transition-colors"
                          title="Edit"
                          data-testid={`edit-btn-${emp.id}`}
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(emp)}
                          className="p-1.5 text-red-400 hover:bg-red-500/20 rounded transition-colors"
                          title="Nonaktifkan"
                          data-testid={`delete-btn-${emp.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between">
          <div className="text-sm text-slate-400">
            Menampilkan {employees.length} dari {total} karyawan
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="border-slate-600 text-slate-300"
              data-testid="prev-page-btn"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm text-slate-300">
              Halaman {page} dari {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="border-slate-600 text-slate-300"
              data-testid="next-page-btn"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
      
      {/* Employee Modal */}
      <EmployeeModal
        isOpen={showModal}
        onClose={() => { setShowModal(false); setSelectedEmployee(null); }}
        employee={selectedEmployee}
        departments={departments}
        positions={positions}
        onSave={handleSaveEmployee}
      />
      
      {/* Detail Modal */}
      {showDetail && detailEmployee && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-lg">
            <div className="p-6 border-b border-slate-700 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-white">Detail Karyawan</h2>
              <button 
                onClick={() => setShowDetail(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400">NIK</p>
                  <p className="text-white font-mono">{detailEmployee.employee_id || detailEmployee.nik || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Status</p>
                  <StatusBadge status={detailEmployee.status || 'active'} />
                </div>
              </div>
              <div>
                <p className="text-sm text-slate-400">Nama Lengkap</p>
                <p className="text-white font-medium">{detailEmployee.full_name || detailEmployee.name}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400">Departemen</p>
                  <p className="text-white">{detailEmployee.department_name || detailEmployee.department || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Posisi</p>
                  <p className="text-white">{detailEmployee.position_name || detailEmployee.jabatan_name || '-'}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400">Email</p>
                  <p className="text-white">{detailEmployee.email || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Telepon</p>
                  <p className="text-white">{detailEmployee.phone || '-'}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400">Tanggal Bergabung</p>
                  <p className="text-white">{detailEmployee.join_date || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Gaji Pokok</p>
                  <p className="text-green-400 font-medium">{formatCurrency(detailEmployee.salary_base)}</p>
                </div>
              </div>
              {detailEmployee.leave_balance && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">Sisa Cuti</p>
                  <div className="grid grid-cols-4 gap-2">
                    <div className="bg-slate-900 rounded p-2 text-center">
                      <p className="text-xs text-slate-400">Tahunan</p>
                      <p className="text-white font-bold">{detailEmployee.leave_balance.annual || 0}</p>
                    </div>
                    <div className="bg-slate-900 rounded p-2 text-center">
                      <p className="text-xs text-slate-400">Sakit</p>
                      <p className="text-white font-bold">{detailEmployee.leave_balance.sick || 0}</p>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Document Upload Section */}
              <DocumentUploadSection 
                employeeId={detailEmployee.id}
                token={localStorage.getItem('token')}
                onRefresh={() => {}}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HREmployees;
