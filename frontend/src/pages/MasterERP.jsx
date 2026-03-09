import React, { useState, useEffect } from 'react';
import { 
  Clock, Plus, Edit, Trash2, Briefcase, MapPin, Settings, DollarSign
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const MasterERP = () => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('shifts');
  const [shifts, setShifts] = useState([]);
  const [jabatan, setJabatan] = useState([]);
  const [lokasi, setLokasi] = useState([]);
  const [payrollRules, setPayrollRules] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('');
  const [editData, setEditData] = useState(null);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      const [shiftsRes, jabatanRes, lokasiRes, rulesRes] = await Promise.all([
        api.get('/api/erp/master/shifts'),
        api.get('/api/erp/master/jabatan'),
        api.get('/api/erp/master/lokasi-absensi'),
        api.get('/api/erp/master/payroll-rules')
      ]);
      setShifts(shiftsRes.data.shifts || []);
      setJabatan(jabatanRes.data.jabatan || []);
      setLokasi(lokasiRes.data.lokasi || []);
      setPayrollRules(rulesRes.data.rules || []);
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat data master', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = (type) => {
    setModalType(type);
    setEditData(null);
    setFormData(getDefaultForm(type));
    setShowModal(true);
  };

  const openEditModal = (type, data) => {
    setModalType(type);
    setEditData(data);
    setFormData({ ...data });
    setShowModal(true);
  };

  const getDefaultForm = (type) => {
    switch (type) {
      case 'shift':
        return { code: '', name: '', start_time: '08:00', end_time: '17:00', break_minutes: 60 };
      case 'jabatan':
        return { code: '', name: '', level: 1, department: '' };
      case 'lokasi':
        return { branch_id: '', branch_name: '', latitude: 0, longitude: 0, radius_meters: 100, address: '' };
      case 'payroll':
        return { 
          jabatan_id: '', jabatan_name: '', gaji_pokok: 0, tunjangan_jabatan: 0,
          tunjangan_transport: 0, tunjangan_makan: 0, bonus_kehadiran_full: 0,
          potongan_telat_per_menit: 1000, potongan_alpha_per_hari: 50000
        };
      default:
        return {};
    }
  };

  const handleSubmit = async () => {
    try {
      let endpoint = '';
      switch (modalType) {
        case 'shift':
          endpoint = editData ? `/api/erp/master/shifts/${editData.id}` : '/api/erp/master/shifts';
          break;
        case 'jabatan':
          endpoint = editData ? `/api/erp/master/jabatan/${editData.id}` : '/api/erp/master/jabatan';
          break;
        case 'lokasi':
          endpoint = editData ? `/api/erp/master/lokasi-absensi/${editData.id}` : '/api/erp/master/lokasi-absensi';
          break;
        case 'payroll':
          endpoint = '/api/erp/master/payroll-rules';
          break;
      }
      
      if (editData) {
        await api.put(endpoint, formData);
      } else {
        await api.post(endpoint, formData);
      }
      
      toast({ title: 'Sukses', description: 'Data berhasil disimpan' });
      setShowModal(false);
      fetchAllData();
    } catch (err) {
      toast({ title: 'Error', description: err.response?.data?.detail || 'Gagal menyimpan', variant: 'destructive' });
    }
  };

  const handleDelete = async (type, id) => {
    if (!window.confirm('Yakin ingin menghapus?')) return;
    try {
      let endpoint = '';
      switch (type) {
        case 'shift': endpoint = `/api/erp/master/shifts/${id}`; break;
        case 'jabatan': endpoint = `/api/erp/master/jabatan/${id}`; break;
        case 'lokasi': endpoint = `/api/erp/master/lokasi-absensi/${id}`; break;
      }
      await api.delete(endpoint);
      toast({ title: 'Sukses', description: 'Data berhasil dihapus' });
      fetchAllData();
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal menghapus', variant: 'destructive' });
    }
  };

  const formatRupiah = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  };

  const renderModalContent = () => {
    switch (modalType) {
      case 'shift':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400">Kode</label>
                <Input value={formData.code || ''} onChange={e => setFormData({...formData, code: e.target.value})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Nama Shift</label>
                <Input value={formData.name || ''} onChange={e => setFormData({...formData, name: e.target.value})} className="bg-red-950/30 border-red-900/30" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-gray-400">Jam Masuk</label>
                <Input type="time" value={formData.start_time || ''} onChange={e => setFormData({...formData, start_time: e.target.value})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Jam Pulang</label>
                <Input type="time" value={formData.end_time || ''} onChange={e => setFormData({...formData, end_time: e.target.value})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Istirahat (menit)</label>
                <Input type="number" value={formData.break_minutes || 0} onChange={e => setFormData({...formData, break_minutes: parseInt(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
            </div>
          </div>
        );
      case 'jabatan':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400">Kode</label>
                <Input value={formData.code || ''} onChange={e => setFormData({...formData, code: e.target.value})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Nama Jabatan</label>
                <Input value={formData.name || ''} onChange={e => setFormData({...formData, name: e.target.value})} className="bg-red-950/30 border-red-900/30" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400">Level</label>
                <Input type="number" value={formData.level || 1} onChange={e => setFormData({...formData, level: parseInt(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Departemen</label>
                <Input value={formData.department || ''} onChange={e => setFormData({...formData, department: e.target.value})} className="bg-red-950/30 border-red-900/30" />
              </div>
            </div>
          </div>
        );
      case 'lokasi':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400">ID Cabang</label>
                <Input value={formData.branch_id || ''} onChange={e => setFormData({...formData, branch_id: e.target.value})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Nama Cabang</label>
                <Input value={formData.branch_name || ''} onChange={e => setFormData({...formData, branch_name: e.target.value})} className="bg-red-950/30 border-red-900/30" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-gray-400">Latitude</label>
                <Input type="number" step="any" value={formData.latitude || 0} onChange={e => setFormData({...formData, latitude: parseFloat(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Longitude</label>
                <Input type="number" step="any" value={formData.longitude || 0} onChange={e => setFormData({...formData, longitude: parseFloat(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Radius (m)</label>
                <Input type="number" value={formData.radius_meters || 100} onChange={e => setFormData({...formData, radius_meters: parseInt(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-400">Alamat</label>
              <Input value={formData.address || ''} onChange={e => setFormData({...formData, address: e.target.value})} className="bg-red-950/30 border-red-900/30" />
            </div>
          </div>
        );
      case 'payroll':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400">ID Jabatan</label>
                <Input value={formData.jabatan_id || ''} onChange={e => setFormData({...formData, jabatan_id: e.target.value})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Nama Jabatan</label>
                <Input value={formData.jabatan_name || ''} onChange={e => setFormData({...formData, jabatan_name: e.target.value})} className="bg-red-950/30 border-red-900/30" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400">Gaji Pokok</label>
                <Input type="number" value={formData.gaji_pokok || 0} onChange={e => setFormData({...formData, gaji_pokok: parseFloat(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Tunj. Jabatan</label>
                <Input type="number" value={formData.tunjangan_jabatan || 0} onChange={e => setFormData({...formData, tunjangan_jabatan: parseFloat(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400">Tunj. Transport</label>
                <Input type="number" value={formData.tunjangan_transport || 0} onChange={e => setFormData({...formData, tunjangan_transport: parseFloat(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Tunj. Makan</label>
                <Input type="number" value={formData.tunjangan_makan || 0} onChange={e => setFormData({...formData, tunjangan_makan: parseFloat(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-gray-400">Bonus Hadir Full</label>
                <Input type="number" value={formData.bonus_kehadiran_full || 0} onChange={e => setFormData({...formData, bonus_kehadiran_full: parseFloat(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Pot. Telat/menit</label>
                <Input type="number" value={formData.potongan_telat_per_menit || 0} onChange={e => setFormData({...formData, potongan_telat_per_menit: parseFloat(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Pot. Alpha/hari</label>
                <Input type="number" value={formData.potongan_alpha_per_hari || 0} onChange={e => setFormData({...formData, potongan_alpha_per_hari: parseFloat(e.target.value)})} className="bg-red-950/30 border-red-900/30" />
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="p-6 space-y-6" data-testid="master-erp-page">
      <div>
        <h1 className="text-2xl font-bold text-amber-100">Master Data ERP</h1>
        <p className="text-gray-400 text-sm">Kelola data master untuk sistem ERP</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-red-950/30">
          <TabsTrigger value="shifts" className="flex items-center gap-2">
            <Clock className="h-4 w-4" /> Shift
          </TabsTrigger>
          <TabsTrigger value="jabatan" className="flex items-center gap-2">
            <Briefcase className="h-4 w-4" /> Jabatan
          </TabsTrigger>
          <TabsTrigger value="lokasi" className="flex items-center gap-2">
            <MapPin className="h-4 w-4" /> Lokasi Absensi
          </TabsTrigger>
          <TabsTrigger value="payroll" className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" /> Aturan Payroll
          </TabsTrigger>
        </TabsList>

        <TabsContent value="shifts" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-amber-200">Master Shift</CardTitle>
              <Button onClick={() => openAddModal('shift')} size="sm" className="bg-gradient-to-r from-red-600 to-amber-600">
                <Plus className="h-4 w-4 mr-1" /> Tambah
              </Button>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead className="bg-red-950/30">
                  <tr className="text-left text-xs text-gray-400">
                    <th className="p-3">Kode</th>
                    <th className="p-3">Nama</th>
                    <th className="p-3">Jam Masuk</th>
                    <th className="p-3">Jam Pulang</th>
                    <th className="p-3">Istirahat</th>
                    <th className="p-3 text-center">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-red-900/20">
                  {shifts.map(s => (
                    <tr key={s.id} className="hover:bg-red-950/20">
                      <td className="p-3 text-sm text-gray-300">{s.code}</td>
                      <td className="p-3 text-sm text-amber-200">{s.name}</td>
                      <td className="p-3 text-sm text-gray-300">{s.start_time}</td>
                      <td className="p-3 text-sm text-gray-300">{s.end_time}</td>
                      <td className="p-3 text-sm text-gray-400">{s.break_minutes} menit</td>
                      <td className="p-3 text-center">
                        <Button variant="ghost" size="sm" onClick={() => openEditModal('shift', s)} className="h-8 w-8 p-0"><Edit className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete('shift', s.id)} className="h-8 w-8 p-0 text-red-400"><Trash2 className="h-4 w-4" /></Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="jabatan" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-amber-200">Master Jabatan</CardTitle>
              <Button onClick={() => openAddModal('jabatan')} size="sm" className="bg-gradient-to-r from-red-600 to-amber-600">
                <Plus className="h-4 w-4 mr-1" /> Tambah
              </Button>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead className="bg-red-950/30">
                  <tr className="text-left text-xs text-gray-400">
                    <th className="p-3">Kode</th>
                    <th className="p-3">Nama</th>
                    <th className="p-3">Level</th>
                    <th className="p-3">Departemen</th>
                    <th className="p-3 text-center">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-red-900/20">
                  {jabatan.map(j => (
                    <tr key={j.id} className="hover:bg-red-950/20">
                      <td className="p-3 text-sm text-gray-300">{j.code}</td>
                      <td className="p-3 text-sm text-amber-200">{j.name}</td>
                      <td className="p-3 text-sm text-gray-300">{j.level}</td>
                      <td className="p-3 text-sm text-gray-400">{j.department}</td>
                      <td className="p-3 text-center">
                        <Button variant="ghost" size="sm" onClick={() => openEditModal('jabatan', j)} className="h-8 w-8 p-0"><Edit className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete('jabatan', j.id)} className="h-8 w-8 p-0 text-red-400"><Trash2 className="h-4 w-4" /></Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="lokasi" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-amber-200">Lokasi Absensi GPS</CardTitle>
              <Button onClick={() => openAddModal('lokasi')} size="sm" className="bg-gradient-to-r from-red-600 to-amber-600">
                <Plus className="h-4 w-4 mr-1" /> Tambah
              </Button>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead className="bg-red-950/30">
                  <tr className="text-left text-xs text-gray-400">
                    <th className="p-3">Cabang</th>
                    <th className="p-3">Koordinat</th>
                    <th className="p-3">Radius</th>
                    <th className="p-3">Alamat</th>
                    <th className="p-3 text-center">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-red-900/20">
                  {lokasi.map(l => (
                    <tr key={l.id} className="hover:bg-red-950/20">
                      <td className="p-3 text-sm text-amber-200">{l.branch_name}</td>
                      <td className="p-3 text-xs text-gray-400 font-mono">{l.latitude}, {l.longitude}</td>
                      <td className="p-3 text-sm text-gray-300">{l.radius_meters}m</td>
                      <td className="p-3 text-sm text-gray-400 truncate max-w-[200px]">{l.address}</td>
                      <td className="p-3 text-center">
                        <Button variant="ghost" size="sm" onClick={() => openEditModal('lokasi', l)} className="h-8 w-8 p-0"><Edit className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete('lokasi', l.id)} className="h-8 w-8 p-0 text-red-400"><Trash2 className="h-4 w-4" /></Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payroll" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-amber-200">Aturan Payroll per Jabatan</CardTitle>
              <Button onClick={() => openAddModal('payroll')} size="sm" className="bg-gradient-to-r from-red-600 to-amber-600">
                <Plus className="h-4 w-4 mr-1" /> Tambah
              </Button>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead className="bg-red-950/30">
                  <tr className="text-left text-xs text-gray-400">
                    <th className="p-3">Jabatan</th>
                    <th className="p-3 text-right">Gaji Pokok</th>
                    <th className="p-3 text-right">Tunj. Jabatan</th>
                    <th className="p-3 text-right">Tunj. Transport</th>
                    <th className="p-3 text-right">Tunj. Makan</th>
                    <th className="p-3 text-right">Bonus Hadir</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-red-900/20">
                  {payrollRules.map(r => (
                    <tr key={r.id} className="hover:bg-red-950/20">
                      <td className="p-3 text-sm text-amber-200">{r.jabatan_name}</td>
                      <td className="p-3 text-sm text-right text-green-400">{formatRupiah(r.gaji_pokok)}</td>
                      <td className="p-3 text-sm text-right text-gray-300">{formatRupiah(r.tunjangan_jabatan)}</td>
                      <td className="p-3 text-sm text-right text-gray-300">{formatRupiah(r.tunjangan_transport)}</td>
                      <td className="p-3 text-sm text-right text-gray-300">{formatRupiah(r.tunjangan_makan)}</td>
                      <td className="p-3 text-sm text-right text-blue-400">{formatRupiah(r.bonus_kehadiran_full)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="bg-[#0f0a0a] border-red-900/30">
          <DialogHeader>
            <DialogTitle className="text-amber-100">
              {editData ? 'Edit' : 'Tambah'} {modalType.charAt(0).toUpperCase() + modalType.slice(1)}
            </DialogTitle>
          </DialogHeader>
          {renderModalContent()}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowModal(false)}>Batal</Button>
            <Button onClick={handleSubmit} className="bg-gradient-to-r from-red-600 to-amber-600">Simpan</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MasterERP;
