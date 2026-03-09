import React, { useState, useEffect } from 'react';
import { 
  Users, Plus, Search, Edit, Trash2, Building2, Phone, Mail,
  Briefcase, Calendar, CreditCard, User, MapPin, FileText
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const Employees = () => {
  const { toast } = useToast();
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [branches, setBranches] = useState([]);
  const [jabatanList, setJabatanList] = useState([]);
  const [search, setSearch] = useState('');
  const [filterBranch, setFilterBranch] = useState('all');
  const [filterStatus, setFilterStatus] = useState('active');
  
  // Modal
  const [showModal, setShowModal] = useState(false);
  const [editData, setEditData] = useState(null);
  const [formData, setFormData] = useState({
    nik: '',
    name: '',
    email: '',
    phone: '',
    whatsapp: '',
    jabatan_id: '',
    jabatan_name: '',
    department: '',
    branch_id: '',
    branch_name: '',
    ktp_number: '',
    birth_date: '',
    birth_place: '',
    gender: '',
    religion: '',
    marital_status: '',
    address: '',
    join_date: '',
    contract_type: 'tetap',
    contract_end_date: '',
    bank_name: '',
    bank_account: '',
    bank_holder: '',
    gaji_pokok: 0,
    tunjangan_total: 0
  });

  useEffect(() => {
    fetchData();
    fetchBranches();
    fetchJabatan();
  }, [search, filterBranch, filterStatus]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (filterBranch !== 'all') params.append('branch_id', filterBranch);
      if (filterStatus !== 'all') params.append('status', filterStatus);
      
      const res = await api.get(`/api/erp/employees?${params.toString()}`);
      setEmployees(res.data.employees || []);
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat data karyawan', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const fetchBranches = async () => {
    try {
      const res = await api.get('/api/branches');
      setBranches(res.data.branches || res.data || []);
    } catch (err) {
      console.error('Error fetching branches:', err);
    }
  };

  const fetchJabatan = async () => {
    try {
      const res = await api.get('/api/erp/master/jabatan');
      setJabatanList(res.data.jabatan || []);
    } catch (err) {
      console.error('Error fetching jabatan:', err);
    }
  };

  const handleBranchChange = (branchId) => {
    const branch = branches.find(b => b.id === branchId);
    if (branch) {
      setFormData(prev => ({
        ...prev,
        branch_id: branch.id,
        branch_name: branch.name
      }));
    }
  };

  const handleJabatanChange = (jabatanId) => {
    const jab = jabatanList.find(j => j.id === jabatanId);
    if (jab) {
      setFormData(prev => ({
        ...prev,
        jabatan_id: jab.id,
        jabatan_name: jab.name,
        department: jab.department || prev.department
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editData) {
        await api.put(`/api/erp/employees/${editData.id}`, formData);
        toast({ title: 'Sukses', description: 'Data karyawan berhasil diupdate' });
      } else {
        await api.post('/api/erp/employees', formData);
        toast({ title: 'Sukses', description: 'Karyawan berhasil ditambahkan' });
      }
      
      setShowModal(false);
      setEditData(null);
      resetForm();
      fetchData();
    } catch (err) {
      toast({ 
        title: 'Error', 
        description: err.response?.data?.detail || 'Gagal menyimpan data karyawan', 
        variant: 'destructive' 
      });
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Yakin ingin menghapus karyawan ini?')) return;
    try {
      await api.delete(`/api/erp/employees/${id}`);
      toast({ title: 'Sukses', description: 'Karyawan berhasil dihapus' });
      fetchData();
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal menghapus karyawan', variant: 'destructive' });
    }
  };

  const resetForm = () => {
    setFormData({
      nik: '',
      name: '',
      email: '',
      phone: '',
      whatsapp: '',
      jabatan_id: '',
      jabatan_name: '',
      department: '',
      branch_id: '',
      branch_name: '',
      ktp_number: '',
      birth_date: '',
      birth_place: '',
      gender: '',
      religion: '',
      marital_status: '',
      address: '',
      join_date: '',
      contract_type: 'tetap',
      contract_end_date: '',
      bank_name: '',
      bank_account: '',
      bank_holder: '',
      gaji_pokok: 0,
      tunjangan_total: 0
    });
  };

  const openEdit = (item) => {
    setEditData(item);
    setFormData({ ...item });
    setShowModal(true);
  };

  const formatRupiah = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  };

  return (
    <div className="p-6 space-y-6" data-testid="employees-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Data Karyawan</h1>
          <p className="text-gray-400 text-sm">Kelola data karyawan perusahaan</p>
        </div>
        <Button 
          onClick={() => { resetForm(); setShowModal(true); }}
          className="bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-700 hover:to-amber-700"
          data-testid="btn-tambah-karyawan"
        >
          <Plus className="h-4 w-4 mr-2" /> Tambah Karyawan
        </Button>
      </div>

      {/* Filters */}
      <Card className="bg-[#0f0a0a] border-red-900/20">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Cari nama, NIK, email..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-10 bg-red-950/30 border-red-900/30"
                />
              </div>
            </div>
            <Select value={filterBranch} onValueChange={setFilterBranch}>
              <SelectTrigger className="w-48 bg-red-950/30 border-red-900/30">
                <SelectValue placeholder="Semua Cabang" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua Cabang</SelectItem>
                {branches.map(b => (
                  <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-40 bg-red-950/30 border-red-900/30">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua Status</SelectItem>
                <SelectItem value="active">Aktif</SelectItem>
                <SelectItem value="resigned">Resign</SelectItem>
                <SelectItem value="terminated">Terminated</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-green-900/30 to-green-800/20 border-green-700/30">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-green-400">{employees.length}</p>
            <p className="text-xs text-gray-400">Total Karyawan</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border-blue-700/30">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-blue-400">
              {employees.filter(e => e.contract_type === 'tetap').length}
            </p>
            <p className="text-xs text-gray-400">Karyawan Tetap</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-amber-900/30 to-amber-800/20 border-amber-700/30">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-amber-400">
              {employees.filter(e => e.contract_type === 'kontrak').length}
            </p>
            <p className="text-xs text-gray-400">Kontrak</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border-purple-700/30">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-purple-400">
              {new Set(employees.map(e => e.branch_id)).size}
            </p>
            <p className="text-xs text-gray-400">Cabang</p>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card className="bg-[#0f0a0a] border-red-900/20">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-red-950/30">
                <tr className="text-left text-xs text-gray-400">
                  <th className="p-3">NIK</th>
                  <th className="p-3">Nama</th>
                  <th className="p-3">Jabatan</th>
                  <th className="p-3">Cabang</th>
                  <th className="p-3">Telepon</th>
                  <th className="p-3">Tipe</th>
                  <th className="p-3 text-right">Gaji Pokok</th>
                  <th className="p-3 text-center">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/20">
                {loading ? (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-gray-400">Loading...</td>
                  </tr>
                ) : employees.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-gray-400">
                      Tidak ada data karyawan
                    </td>
                  </tr>
                ) : employees.map((emp) => (
                  <tr key={emp.id} className="hover:bg-red-950/20">
                    <td className="p-3 text-sm text-gray-300 font-mono">{emp.nik}</td>
                    <td className="p-3">
                      <div>
                        <p className="text-sm font-medium text-amber-200">{emp.name}</p>
                        <p className="text-xs text-gray-500">{emp.email}</p>
                      </div>
                    </td>
                    <td className="p-3">
                      <div>
                        <p className="text-sm text-gray-300">{emp.jabatan_name || '-'}</p>
                        <p className="text-xs text-gray-500">{emp.department}</p>
                      </div>
                    </td>
                    <td className="p-3 text-sm text-gray-300">{emp.branch_name || '-'}</td>
                    <td className="p-3 text-sm text-gray-400">{emp.phone || emp.whatsapp || '-'}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        emp.contract_type === 'tetap' 
                          ? 'bg-green-500/20 text-green-400' 
                          : emp.contract_type === 'kontrak'
                          ? 'bg-yellow-500/20 text-yellow-400'
                          : 'bg-blue-500/20 text-blue-400'
                      }`}>
                        {emp.contract_type}
                      </span>
                    </td>
                    <td className="p-3 text-sm text-right text-green-400">{formatRupiah(emp.gaji_pokok)}</td>
                    <td className="p-3">
                      <div className="flex items-center justify-center gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => openEdit(emp)}
                          className="h-8 w-8 p-0 text-gray-400 hover:text-amber-400"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleDelete(emp.id)}
                          className="h-8 w-8 p-0 text-gray-400 hover:text-red-400"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-[#0f0a0a] border-red-900/30">
          <DialogHeader>
            <DialogTitle className="text-amber-100">
              {editData ? 'Edit Karyawan' : 'Tambah Karyawan Baru'}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit}>
            <Tabs defaultValue="personal" className="w-full">
              <TabsList className="grid w-full grid-cols-4 bg-red-950/30">
                <TabsTrigger value="personal">Personal</TabsTrigger>
                <TabsTrigger value="employment">Kepegawaian</TabsTrigger>
                <TabsTrigger value="bank">Bank</TabsTrigger>
                <TabsTrigger value="salary">Gaji</TabsTrigger>
              </TabsList>

              <TabsContent value="personal" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">NIK (Nomor Induk Karyawan) *</label>
                    <Input
                      value={formData.nik}
                      onChange={(e) => setFormData({...formData, nik: e.target.value})}
                      className="bg-red-950/30 border-red-900/30"
                      required
                      placeholder="EMP001"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Nama Lengkap *</label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      className="bg-red-950/30 border-red-900/30"
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">Email</label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      className="bg-red-950/30 border-red-900/30"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Telepon</label>
                    <Input
                      value={formData.phone}
                      onChange={(e) => setFormData({...formData, phone: e.target.value})}
                      className="bg-red-950/30 border-red-900/30"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">WhatsApp</label>
                    <Input
                      value={formData.whatsapp}
                      onChange={(e) => setFormData({...formData, whatsapp: e.target.value})}
                      className="bg-red-950/30 border-red-900/30"
                      placeholder="628xxxxxxxxxx"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">No. KTP</label>
                    <Input
                      value={formData.ktp_number}
                      onChange={(e) => setFormData({...formData, ktp_number: e.target.value})}
                      className="bg-red-950/30 border-red-900/30"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">Tempat Lahir</label>
                    <Input
                      value={formData.birth_place}
                      onChange={(e) => setFormData({...formData, birth_place: e.target.value})}
                      className="bg-red-950/30 border-red-900/30"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Tanggal Lahir</label>
                    <Input
                      type="date"
                      value={formData.birth_date}
                      onChange={(e) => setFormData({...formData, birth_date: e.target.value})}
                      className="bg-red-950/30 border-red-900/30"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Jenis Kelamin</label>
                    <Select value={formData.gender} onValueChange={(v) => setFormData({...formData, gender: v})}>
                      <SelectTrigger className="bg-red-950/30 border-red-900/30">
                        <SelectValue placeholder="Pilih" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Laki-laki">Laki-laki</SelectItem>
                        <SelectItem value="Perempuan">Perempuan</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-gray-400">Alamat</label>
                  <Input
                    value={formData.address}
                    onChange={(e) => setFormData({...formData, address: e.target.value})}
                    className="bg-red-950/30 border-red-900/30"
                  />
                </div>
              </TabsContent>

              <TabsContent value="employment" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">Jabatan</label>
                    <Select value={formData.jabatan_id} onValueChange={handleJabatanChange}>
                      <SelectTrigger className="bg-red-950/30 border-red-900/30">
                        <SelectValue placeholder="Pilih Jabatan" />
                      </SelectTrigger>
                      <SelectContent>
                        {jabatanList.map(j => (
                          <SelectItem key={j.id} value={j.id}>{j.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Departemen</label>
                    <Input
                      value={formData.department}
                      onChange={(e) => setFormData({...formData, department: e.target.value})}
                      className="bg-red-950/30 border-red-900/30"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">Cabang</label>
                    <Select value={formData.branch_id} onValueChange={handleBranchChange}>
                      <SelectTrigger className="bg-red-950/30 border-red-900/30">
                        <SelectValue placeholder="Pilih Cabang" />
                      </SelectTrigger>
                      <SelectContent>
                        {branches.map(b => (
                          <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Tanggal Bergabung</label>
                    <Input
                      type="date"
                      value={formData.join_date}
                      onChange={(e) => setFormData({...formData, join_date: e.target.value})}
                      className="bg-red-950/30 border-red-900/30"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">Tipe Kontrak</label>
                    <Select value={formData.contract_type} onValueChange={(v) => setFormData({...formData, contract_type: v})}>
                      <SelectTrigger className="bg-red-950/30 border-red-900/30">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="tetap">Karyawan Tetap</SelectItem>
                        <SelectItem value="kontrak">Kontrak</SelectItem>
                        <SelectItem value="magang">Magang</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {formData.contract_type !== 'tetap' && (
                    <div>
                      <label className="text-xs text-gray-400">Tanggal Berakhir Kontrak</label>
                      <Input
                        type="date"
                        value={formData.contract_end_date}
                        onChange={(e) => setFormData({...formData, contract_end_date: e.target.value})}
                        className="bg-red-950/30 border-red-900/30"
                      />
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="bank" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">Nama Bank</label>
                    <Select value={formData.bank_name} onValueChange={(v) => setFormData({...formData, bank_name: v})}>
                      <SelectTrigger className="bg-red-950/30 border-red-900/30">
                        <SelectValue placeholder="Pilih Bank" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="BCA">BCA</SelectItem>
                        <SelectItem value="BNI">BNI</SelectItem>
                        <SelectItem value="BRI">BRI</SelectItem>
                        <SelectItem value="Mandiri">Mandiri</SelectItem>
                        <SelectItem value="CIMB">CIMB Niaga</SelectItem>
                        <SelectItem value="BSI">BSI</SelectItem>
                        <SelectItem value="Permata">Permata</SelectItem>
                        <SelectItem value="Lainnya">Lainnya</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Nomor Rekening</label>
                    <Input
                      value={formData.bank_account}
                      onChange={(e) => setFormData({...formData, bank_account: e.target.value})}
                      className="bg-red-950/30 border-red-900/30"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-gray-400">Nama Pemilik Rekening</label>
                  <Input
                    value={formData.bank_holder}
                    onChange={(e) => setFormData({...formData, bank_holder: e.target.value})}
                    className="bg-red-950/30 border-red-900/30"
                  />
                </div>
              </TabsContent>

              <TabsContent value="salary" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">Gaji Pokok</label>
                    <Input
                      type="number"
                      value={formData.gaji_pokok}
                      onChange={(e) => setFormData({...formData, gaji_pokok: parseFloat(e.target.value) || 0})}
                      className="bg-red-950/30 border-red-900/30"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Total Tunjangan</label>
                    <Input
                      type="number"
                      value={formData.tunjangan_total}
                      onChange={(e) => setFormData({...formData, tunjangan_total: parseFloat(e.target.value) || 0})}
                      className="bg-red-950/30 border-red-900/30"
                    />
                  </div>
                </div>
                <div className="p-4 bg-green-900/20 rounded-lg">
                  <p className="text-sm text-gray-400">Estimasi Take Home Pay:</p>
                  <p className="text-2xl font-bold text-green-400">
                    {formatRupiah((formData.gaji_pokok || 0) + (formData.tunjangan_total || 0))}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">*Sebelum potongan</p>
                </div>
              </TabsContent>
            </Tabs>

            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
                Batal
              </Button>
              <Button type="submit" className="bg-gradient-to-r from-red-600 to-amber-600">
                {editData ? 'Update' : 'Simpan'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Employees;
