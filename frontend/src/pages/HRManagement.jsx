import React, { useState, useEffect, useRef } from 'react';
import { 
  Users, Upload, FileText, GraduationCap, Building2, Award, AlertTriangle,
  Plus, Edit, Trash2, Download, Eye, CheckCircle, XCircle, Clock, Calendar,
  UserPlus, FolderOpen, FileCheck, ChevronRight, Search, Filter, MoreVertical
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const HRManagement = () => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('employees');
  const [loading, setLoading] = useState(true);
  
  // Data states
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [trainings, setTrainings] = useState([]);
  const [orgStructure, setOrgStructure] = useState([]);
  
  // Modal states
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('');
  const [formData, setFormData] = useState({});
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  
  // Upload state
  const fileInputRef = useRef(null);
  const [uploadProgress, setUploadProgress] = useState(null);
  
  // Search & filter
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDept, setFilterDept] = useState('');

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      const [empRes, deptRes, trainRes, orgRes] = await Promise.all([
        api.get('/api/erp/employees?status=active'),
        api.get('/api/hr/departments'),
        api.get('/api/hr/trainings'),
        api.get('/api/hr/organization/structure')
      ]);
      setEmployees(empRes.data.employees || []);
      setDepartments(deptRes.data.departments || []);
      setTrainings(trainRes.data.trainings || []);
      setOrgStructure(orgRes.data.structure || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Mass Upload Handler
  const handleMassUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploadProgress('uploading');
      const res = await api.post('/api/hr/employees/mass-upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      toast({
        title: 'Upload Berhasil',
        description: res.data.message
      });
      setUploadProgress(null);
      fetchAllData();
    } catch (err) {
      toast({
        title: 'Gagal Upload',
        description: err.response?.data?.detail || 'Error saat upload',
        variant: 'destructive'
      });
      setUploadProgress(null);
    }
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Generate Document
  const generateDocument = async (docType, employeeId) => {
    try {
      const res = await api.get(`/api/hr/documents/generate/${docType}/${employeeId}`);
      
      // Create downloadable text file
      const blob = new Blob([res.data.content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${docType}_${res.data.employee}.txt`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({ title: 'Dokumen dibuat', description: `${docType} berhasil diunduh` });
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal generate dokumen', variant: 'destructive' });
    }
  };

  // Training functions
  const openTrainingModal = (training = null) => {
    setModalType('training');
    setFormData(training || {
      title: '', description: '', trainer: '', training_type: 'internal',
      start_date: '', end_date: '', location: '', max_participants: 50, is_mandatory: false
    });
    setShowModal(true);
  };

  const saveTraining = async () => {
    try {
      if (formData.id) {
        await api.put(`/api/hr/trainings/${formData.id}`, formData);
      } else {
        await api.post('/api/hr/trainings', formData);
      }
      toast({ title: 'Sukses', description: 'Training berhasil disimpan' });
      setShowModal(false);
      fetchAllData();
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal menyimpan training', variant: 'destructive' });
    }
  };

  // Employee detail modal
  const viewEmployeeDetail = async (emp) => {
    try {
      const [relRes, docsRes, contractsRes, warningsRes] = await Promise.all([
        api.get(`/api/hr/employees/${emp.id}/relations`),
        api.get(`/api/hr/employees/${emp.id}/documents`),
        api.get(`/api/hr/employees/${emp.id}/contracts`),
        api.get(`/api/hr/employees/${emp.id}/warnings`)
      ]);
      
      setSelectedEmployee({
        ...emp,
        relations: relRes.data,
        documents: docsRes.data.documents || [],
        contracts: contractsRes.data.contracts || [],
        warnings: warningsRes.data.warnings || []
      });
      setModalType('employee-detail');
      setShowModal(true);
    } catch (err) {
      setSelectedEmployee(emp);
      setModalType('employee-detail');
      setShowModal(true);
    }
  };

  // Filter employees
  const filteredEmployees = employees.filter(emp => {
    const matchSearch = emp.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       emp.nik?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchDept = !filterDept || emp.department === filterDept;
    return matchSearch && matchDept;
  });

  const formatRupiah = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  };

  return (
    <div className="p-6 space-y-6" data-testid="hr-management-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">HR Management</h1>
          <p className="text-gray-400 text-sm">Kelola karyawan, training, dan struktur organisasi</p>
        </div>
        <div className="flex gap-2">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".xlsx,.xls,.csv"
            onChange={handleMassUpload}
          />
          <Button 
            onClick={() => fileInputRef.current?.click()}
            className="bg-blue-600 hover:bg-blue-700"
            disabled={uploadProgress === 'uploading'}
          >
            <Upload className="h-4 w-4 mr-2" />
            {uploadProgress === 'uploading' ? 'Uploading...' : 'Mass Upload'}
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-red-950/30">
          <TabsTrigger value="employees" className="flex items-center gap-2">
            <Users className="h-4 w-4" /> Karyawan
          </TabsTrigger>
          <TabsTrigger value="training" className="flex items-center gap-2">
            <GraduationCap className="h-4 w-4" /> Training
          </TabsTrigger>
          <TabsTrigger value="structure" className="flex items-center gap-2">
            <Building2 className="h-4 w-4" /> Struktur Organisasi
          </TabsTrigger>
          <TabsTrigger value="documents" className="flex items-center gap-2">
            <FileText className="h-4 w-4" /> Dokumen HR
          </TabsTrigger>
        </TabsList>

        {/* EMPLOYEES TAB */}
        <TabsContent value="employees" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-amber-200">Data Karyawan ({filteredEmployees.length})</CardTitle>
              <div className="flex gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
                  <Input
                    placeholder="Cari nama/NIK..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="pl-9 w-[200px] bg-red-950/30 border-red-900/30"
                  />
                </div>
                <select
                  value={filterDept}
                  onChange={e => setFilterDept(e.target.value)}
                  className="bg-red-950/30 border border-red-900/30 rounded-md px-3 py-2 text-sm text-gray-300"
                >
                  <option value="">Semua Dept</option>
                  {departments.map(d => (
                    <option key={d.id} value={d.name}>{d.name}</option>
                  ))}
                </select>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-red-950/30">
                    <tr className="text-left text-xs text-gray-400">
                      <th className="p-3">NIK</th>
                      <th className="p-3">Nama</th>
                      <th className="p-3">Jabatan</th>
                      <th className="p-3">Departemen</th>
                      <th className="p-3">Cabang</th>
                      <th className="p-3 text-right">Gaji Pokok</th>
                      <th className="p-3 text-center">Status</th>
                      <th className="p-3 text-center">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-900/20">
                    {filteredEmployees.map(emp => (
                      <tr key={emp.id} className="hover:bg-red-950/20">
                        <td className="p-3 text-sm font-mono text-gray-400">{emp.nik}</td>
                        <td className="p-3 text-sm text-amber-200 font-medium">{emp.name}</td>
                        <td className="p-3 text-sm text-gray-300">{emp.jabatan_name}</td>
                        <td className="p-3 text-sm text-gray-400">{emp.department}</td>
                        <td className="p-3 text-sm text-gray-400">{emp.branch_name}</td>
                        <td className="p-3 text-sm text-right text-green-400">{formatRupiah(emp.gaji_pokok)}</td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs ${emp.status === 'active' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                            {emp.status}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <Button variant="ghost" size="sm" onClick={() => viewEmployeeDetail(emp)} className="h-8 w-8 p-0">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* TRAINING TAB */}
        <TabsContent value="training" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-amber-200">Program Training</CardTitle>
              <Button onClick={() => openTrainingModal()} size="sm" className="bg-gradient-to-r from-red-600 to-amber-600">
                <Plus className="h-4 w-4 mr-1" /> Tambah Training
              </Button>
            </CardHeader>
            <CardContent>
              {trainings.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <GraduationCap className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Belum ada program training</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {trainings.map(t => (
                    <Card key={t.id} className="bg-red-950/20 border-red-900/20">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-medium text-amber-200">{t.title}</h3>
                          <span className={`text-xs px-2 py-1 rounded ${
                            t.status === 'scheduled' ? 'bg-blue-900/30 text-blue-400' :
                            t.status === 'ongoing' ? 'bg-yellow-900/30 text-yellow-400' :
                            'bg-green-900/30 text-green-400'
                          }`}>
                            {t.status}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 mb-2">{t.description}</p>
                        <div className="text-xs text-gray-500 space-y-1">
                          <p><Calendar className="inline h-3 w-3 mr-1" /> {t.start_date} - {t.end_date}</p>
                          <p><Users className="inline h-3 w-3 mr-1" /> {t.participant_count || 0}/{t.max_participants} peserta</p>
                        </div>
                        <Button variant="outline" size="sm" className="w-full mt-3" onClick={() => openTrainingModal(t)}>
                          <Edit className="h-3 w-3 mr-1" /> Kelola
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ORGANIZATION STRUCTURE TAB */}
        <TabsContent value="structure" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader>
              <CardTitle className="text-lg text-amber-200">Struktur Organisasi</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {orgStructure.map(dept => (
                  <Card key={dept.id} className="bg-red-950/20 border-red-900/20">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Building2 className="h-5 w-5 text-amber-500" />
                        <div>
                          <h3 className="font-medium text-amber-200">{dept.name}</h3>
                          <p className="text-xs text-gray-500">{dept.code}</p>
                        </div>
                      </div>
                      <div className="text-sm text-gray-400 mb-2">
                        Total: {dept.total_employees} karyawan
                      </div>
                      {dept.positions?.map((pos, idx) => (
                        <div key={idx} className="ml-2 border-l border-red-900/30 pl-3 py-1">
                          <p className="text-sm text-gray-300">{pos.name} ({pos.count})</p>
                          {pos.employees?.slice(0, 3).map(emp => (
                            <p key={emp.id} className="text-xs text-gray-500 ml-2">• {emp.name}</p>
                          ))}
                          {pos.employees?.length > 3 && (
                            <p className="text-xs text-gray-600 ml-2">+{pos.employees.length - 3} lainnya</p>
                          )}
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* HR DOCUMENTS TAB */}
        <TabsContent value="documents" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader>
              <CardTitle className="text-lg text-amber-200">Generator Dokumen HR</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="bg-red-950/20 border-red-900/20">
                  <CardContent className="p-4 text-center">
                    <FileCheck className="h-12 w-12 mx-auto mb-3 text-green-500" />
                    <h3 className="font-medium text-amber-200 mb-2">SK Pengangkatan</h3>
                    <p className="text-xs text-gray-400 mb-4">Surat Keputusan pengangkatan karyawan</p>
                    <select 
                      className="w-full bg-red-950/30 border border-red-900/30 rounded px-3 py-2 text-sm text-gray-300 mb-2"
                      onChange={(e) => e.target.value && generateDocument('sk_pengangkatan', e.target.value)}
                    >
                      <option value="">Pilih Karyawan</option>
                      {employees.map(emp => (
                        <option key={emp.id} value={emp.id}>{emp.name} - {emp.nik}</option>
                      ))}
                    </select>
                  </CardContent>
                </Card>

                <Card className="bg-red-950/20 border-red-900/20">
                  <CardContent className="p-4 text-center">
                    <AlertTriangle className="h-12 w-12 mx-auto mb-3 text-yellow-500" />
                    <h3 className="font-medium text-amber-200 mb-2">Surat Peringatan</h3>
                    <p className="text-xs text-gray-400 mb-4">SP1, SP2, SP3 untuk karyawan</p>
                    <select 
                      className="w-full bg-red-950/30 border border-red-900/30 rounded px-3 py-2 text-sm text-gray-300 mb-2"
                      onChange={(e) => e.target.value && generateDocument('surat_peringatan', e.target.value)}
                    >
                      <option value="">Pilih Karyawan</option>
                      {employees.map(emp => (
                        <option key={emp.id} value={emp.id}>{emp.name} - {emp.nik}</option>
                      ))}
                    </select>
                  </CardContent>
                </Card>

                <Card className="bg-red-950/20 border-red-900/20">
                  <CardContent className="p-4 text-center">
                    <Award className="h-12 w-12 mx-auto mb-3 text-blue-500" />
                    <h3 className="font-medium text-amber-200 mb-2">Surat Referensi</h3>
                    <p className="text-xs text-gray-400 mb-4">Surat keterangan kerja</p>
                    <select 
                      className="w-full bg-red-950/30 border border-red-900/30 rounded px-3 py-2 text-sm text-gray-300 mb-2"
                      onChange={(e) => e.target.value && generateDocument('surat_referensi', e.target.value)}
                    >
                      <option value="">Pilih Karyawan</option>
                      {employees.map(emp => (
                        <option key={emp.id} value={emp.id}>{emp.name} - {emp.nik}</option>
                      ))}
                    </select>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* MODALS */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="bg-[#0f0a0a] border-red-900/30 max-w-2xl max-h-[80vh] overflow-y-auto">
          {modalType === 'training' && (
            <>
              <DialogHeader>
                <DialogTitle className="text-amber-100">{formData.id ? 'Edit' : 'Tambah'} Training</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-xs text-gray-400">Judul Training</label>
                  <Input 
                    value={formData.title || ''} 
                    onChange={e => setFormData({...formData, title: e.target.value})} 
                    className="bg-red-950/30 border-red-900/30" 
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Deskripsi</label>
                  <textarea 
                    value={formData.description || ''} 
                    onChange={e => setFormData({...formData, description: e.target.value})} 
                    className="w-full bg-red-950/30 border border-red-900/30 rounded-md px-3 py-2 text-sm text-gray-300"
                    rows={3}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">Trainer</label>
                    <Input 
                      value={formData.trainer || ''} 
                      onChange={e => setFormData({...formData, trainer: e.target.value})} 
                      className="bg-red-950/30 border-red-900/30" 
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Tipe</label>
                    <select 
                      value={formData.training_type || 'internal'}
                      onChange={e => setFormData({...formData, training_type: e.target.value})}
                      className="w-full bg-red-950/30 border border-red-900/30 rounded-md px-3 py-2 text-sm text-gray-300"
                    >
                      <option value="internal">Internal</option>
                      <option value="external">External</option>
                      <option value="online">Online</option>
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">Tanggal Mulai</label>
                    <Input 
                      type="date"
                      value={formData.start_date || ''} 
                      onChange={e => setFormData({...formData, start_date: e.target.value})} 
                      className="bg-red-950/30 border-red-900/30" 
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Tanggal Selesai</label>
                    <Input 
                      type="date"
                      value={formData.end_date || ''} 
                      onChange={e => setFormData({...formData, end_date: e.target.value})} 
                      className="bg-red-950/30 border-red-900/30" 
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">Lokasi</label>
                    <Input 
                      value={formData.location || ''} 
                      onChange={e => setFormData({...formData, location: e.target.value})} 
                      className="bg-red-950/30 border-red-900/30" 
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Max Peserta</label>
                    <Input 
                      type="number"
                      value={formData.max_participants || 50} 
                      onChange={e => setFormData({...formData, max_participants: parseInt(e.target.value)})} 
                      className="bg-red-950/30 border-red-900/30" 
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowModal(false)}>Batal</Button>
                <Button onClick={saveTraining} className="bg-gradient-to-r from-red-600 to-amber-600">Simpan</Button>
              </DialogFooter>
            </>
          )}

          {modalType === 'employee-detail' && selectedEmployee && (
            <>
              <DialogHeader>
                <DialogTitle className="text-amber-100">Detail Karyawan</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="flex items-center gap-4 p-4 bg-red-950/20 rounded-lg">
                  <div className="h-16 w-16 rounded-full bg-amber-900/30 flex items-center justify-center">
                    <Users className="h-8 w-8 text-amber-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-amber-200">{selectedEmployee.name}</h3>
                    <p className="text-sm text-gray-400">{selectedEmployee.jabatan_name} - {selectedEmployee.department}</p>
                    <p className="text-xs text-gray-500">NIK: {selectedEmployee.nik}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-red-950/20 rounded">
                    <p className="text-xs text-gray-500">Email</p>
                    <p className="text-sm text-gray-300">{selectedEmployee.email || '-'}</p>
                  </div>
                  <div className="p-3 bg-red-950/20 rounded">
                    <p className="text-xs text-gray-500">Phone</p>
                    <p className="text-sm text-gray-300">{selectedEmployee.phone || '-'}</p>
                  </div>
                  <div className="p-3 bg-red-950/20 rounded">
                    <p className="text-xs text-gray-500">Cabang</p>
                    <p className="text-sm text-gray-300">{selectedEmployee.branch_name || '-'}</p>
                  </div>
                  <div className="p-3 bg-red-950/20 rounded">
                    <p className="text-xs text-gray-500">Gaji Pokok</p>
                    <p className="text-sm text-green-400">{formatRupiah(selectedEmployee.gaji_pokok)}</p>
                  </div>
                </div>

                {/* Relations */}
                {selectedEmployee.relations && (
                  <div className="p-3 bg-red-950/20 rounded">
                    <h4 className="text-sm font-medium text-amber-200 mb-2">Relasi</h4>
                    {selectedEmployee.relations.supervisor && (
                      <p className="text-xs text-gray-400">Supervisor: <span className="text-gray-300">{selectedEmployee.relations.supervisor.name}</span></p>
                    )}
                    {selectedEmployee.relations.subordinates?.length > 0 && (
                      <p className="text-xs text-gray-400">Bawahan: {selectedEmployee.relations.subordinates.length} orang</p>
                    )}
                  </div>
                )}

                {/* Documents */}
                {selectedEmployee.documents?.length > 0 && (
                  <div className="p-3 bg-red-950/20 rounded">
                    <h4 className="text-sm font-medium text-amber-200 mb-2">Dokumen ({selectedEmployee.documents.length})</h4>
                    <div className="space-y-1">
                      {selectedEmployee.documents.map(doc => (
                        <div key={doc.id} className="flex justify-between items-center text-xs">
                          <span className="text-gray-400">{doc.document_type}: {doc.document_name}</span>
                          {doc.is_expired && <span className="text-red-400">Expired</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Warnings */}
                {selectedEmployee.warnings?.length > 0 && (
                  <div className="p-3 bg-red-900/20 rounded border border-red-800/30">
                    <h4 className="text-sm font-medium text-red-400 mb-2">Peringatan ({selectedEmployee.warnings.length})</h4>
                    {selectedEmployee.warnings.map(w => (
                      <div key={w.id} className="text-xs text-gray-400">
                        {w.warning_type.toUpperCase()}: {w.reason} ({w.issued_date})
                      </div>
                    ))}
                  </div>
                )}

                {/* Quick Actions */}
                <div className="flex gap-2 pt-2">
                  <Button size="sm" variant="outline" onClick={() => generateDocument('sk_pengangkatan', selectedEmployee.id)}>
                    <FileText className="h-3 w-3 mr-1" /> SK
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => generateDocument('surat_referensi', selectedEmployee.id)}>
                    <Award className="h-3 w-3 mr-1" /> Referensi
                  </Button>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowModal(false)}>Tutup</Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default HRManagement;
