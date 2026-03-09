import React, { useState, useEffect } from 'react';
import { 
  Banknote, Plus, Search, Filter, Calendar, Building2, User,
  CheckCircle, XCircle, Clock, AlertTriangle, Eye, Edit, Download
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const SetoranHarian = () => {
  const { toast } = useToast();
  const [setoran, setSetoran] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [branches, setBranches] = useState([]);
  const [employees, setEmployees] = useState([]);
  
  // Filters
  const [tanggal, setTanggal] = useState(new Date().toISOString().split('T')[0]);
  const [filterBranch, setFilterBranch] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  
  // Modal
  const [showModal, setShowModal] = useState(false);
  const [editData, setEditData] = useState(null);
  const [formData, setFormData] = useState({
    tanggal: new Date().toISOString().split('T')[0],
    jam_buka: '08:00',
    jam_tutup: '21:00',
    branch_id: '',
    branch_code: '',
    branch_name: '',
    penjaga_id: '',
    penjaga_name: '',
    shift: 'full',
    total_penjualan: 0,
    total_transaksi: 0,
    penjualan_cash: 0,
    penjualan_transfer: 0,
    penjualan_ewallet: 0,
    penjualan_debit: 0,
    penjualan_credit: 0,
    penjualan_piutang: 0,
    total_setoran: 0,
    metode_setoran: 'cash',
    rekening_tujuan: '',
    catatan_penjaga: ''
  });

  useEffect(() => {
    fetchData();
    fetchBranches();
    fetchEmployees();
  }, [tanggal, filterBranch, filterStatus]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append('tanggal', tanggal);
      if (filterBranch !== 'all') params.append('branch_id', filterBranch);
      if (filterStatus !== 'all') params.append('status', filterStatus);
      
      const res = await api.get(`/api/erp/setoran?${params.toString()}`);
      setSetoran(res.data.setoran || []);
      setSummary(res.data.summary || {});
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat data setoran', variant: 'destructive' });
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

  const fetchEmployees = async () => {
    try {
      const res = await api.get('/api/erp/employees');
      setEmployees(res.data.employees || []);
    } catch (err) {
      console.error('Error fetching employees:', err);
    }
  };

  const handleBranchChange = (branchId) => {
    const branch = branches.find(b => b.id === branchId);
    if (branch) {
      setFormData(prev => ({
        ...prev,
        branch_id: branch.id,
        branch_code: branch.code || '',
        branch_name: branch.name
      }));
    }
  };

  const handleEmployeeChange = (empId) => {
    const emp = employees.find(e => e.id === empId);
    if (emp) {
      setFormData(prev => ({
        ...prev,
        penjaga_id: emp.id,
        penjaga_name: emp.name
      }));
    }
  };

  const calculateTotal = () => {
    const cash = parseFloat(formData.penjualan_cash) || 0;
    const transfer = parseFloat(formData.penjualan_transfer) || 0;
    const ewallet = parseFloat(formData.penjualan_ewallet) || 0;
    const debit = parseFloat(formData.penjualan_debit) || 0;
    const credit = parseFloat(formData.penjualan_credit) || 0;
    const piutang = parseFloat(formData.penjualan_piutang) || 0;
    return cash + transfer + ewallet + debit + credit + piutang;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        total_penjualan: calculateTotal(),
        input_by_id: 'current-user',
        input_by_name: 'Admin'
      };
      
      if (editData) {
        await api.put(`/api/erp/setoran/${editData.id}`, data);
        toast({ title: 'Sukses', description: 'Setoran berhasil diupdate' });
      } else {
        await api.post('/api/erp/setoran', data);
        toast({ title: 'Sukses', description: 'Setoran berhasil disimpan' });
      }
      
      setShowModal(false);
      setEditData(null);
      resetForm();
      fetchData();
    } catch (err) {
      toast({ 
        title: 'Error', 
        description: err.response?.data?.detail || 'Gagal menyimpan setoran', 
        variant: 'destructive' 
      });
    }
  };

  const resetForm = () => {
    setFormData({
      tanggal: new Date().toISOString().split('T')[0],
      jam_buka: '08:00',
      jam_tutup: '21:00',
      branch_id: '',
      branch_code: '',
      branch_name: '',
      penjaga_id: '',
      penjaga_name: '',
      shift: 'full',
      total_penjualan: 0,
      total_transaksi: 0,
      penjualan_cash: 0,
      penjualan_transfer: 0,
      penjualan_ewallet: 0,
      penjualan_debit: 0,
      penjualan_credit: 0,
      penjualan_piutang: 0,
      total_setoran: 0,
      metode_setoran: 'cash',
      rekening_tujuan: '',
      catatan_penjaga: ''
    });
  };

  const openEdit = (item) => {
    setEditData(item);
    setFormData({
      ...item
    });
    setShowModal(true);
  };

  const getStatusBadge = (status, selisih) => {
    if (status === 'approved') {
      return <span className="px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400">Approved</span>;
    }
    if (status === 'rejected') {
      return <span className="px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400">Ditolak</span>;
    }
    if (selisih < 0) {
      return <span className="px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400">Minus</span>;
    }
    if (selisih > 0) {
      return <span className="px-2 py-1 text-xs rounded-full bg-blue-500/20 text-blue-400">Plus</span>;
    }
    return <span className="px-2 py-1 text-xs rounded-full bg-yellow-500/20 text-yellow-400">Pending</span>;
  };

  const formatRupiah = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  };

  return (
    <div className="p-6 space-y-6" data-testid="setoran-harian-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Setoran Harian</h1>
          <p className="text-gray-400 text-sm">Input dan monitoring setoran harian cabang</p>
        </div>
        <Button 
          onClick={() => { resetForm(); setShowModal(true); }}
          className="bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-700 hover:to-amber-700"
          data-testid="btn-tambah-setoran"
        >
          <Plus className="h-4 w-4 mr-2" /> Input Setoran
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="bg-gradient-to-br from-green-900/30 to-green-800/20 border-green-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/20 rounded-lg">
                <Banknote className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Total Penjualan</p>
                <p className="text-lg font-bold text-green-400">{formatRupiah(summary.total_penjualan)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border-blue-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <CheckCircle className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Total Setoran</p>
                <p className="text-lg font-bold text-blue-400">{formatRupiah(summary.total_setoran)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-900/30 to-red-800/20 border-red-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-500/20 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Total Minus</p>
                <p className="text-lg font-bold text-red-400">{formatRupiah(Math.abs(summary.total_minus || 0))}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-cyan-900/30 to-cyan-800/20 border-cyan-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-cyan-500/20 rounded-lg">
                <Plus className="h-5 w-5 text-cyan-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Total Plus</p>
                <p className="text-lg font-bold text-cyan-400">{formatRupiah(summary.total_plus)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-900/30 to-amber-800/20 border-amber-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <Building2 className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Jumlah Setoran</p>
                <p className="text-lg font-bold text-amber-400">{setoran.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-[#0f0a0a] border-red-900/20">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-400" />
              <Input
                type="date"
                value={tanggal}
                onChange={(e) => setTanggal(e.target.value)}
                className="w-40 bg-red-950/30 border-red-900/30"
              />
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
                <SelectValue placeholder="Semua Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="rejected">Ditolak</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card className="bg-[#0f0a0a] border-red-900/20">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-red-950/30">
                <tr className="text-left text-xs text-gray-400">
                  <th className="p-3">Tanggal</th>
                  <th className="p-3">Cabang</th>
                  <th className="p-3">Penjaga</th>
                  <th className="p-3">Shift</th>
                  <th className="p-3 text-right">Penjualan</th>
                  <th className="p-3 text-right">Setoran</th>
                  <th className="p-3 text-right">Selisih</th>
                  <th className="p-3 text-center">Status</th>
                  <th className="p-3 text-center">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/20">
                {loading ? (
                  <tr>
                    <td colSpan="9" className="p-8 text-center text-gray-400">Loading...</td>
                  </tr>
                ) : setoran.length === 0 ? (
                  <tr>
                    <td colSpan="9" className="p-8 text-center text-gray-400">
                      Tidak ada data setoran untuk tanggal ini
                    </td>
                  </tr>
                ) : setoran.map((item) => (
                  <tr key={item.id} className="hover:bg-red-950/20">
                    <td className="p-3 text-sm text-gray-300">{item.tanggal}</td>
                    <td className="p-3">
                      <div>
                        <p className="text-sm font-medium text-amber-200">{item.branch_name}</p>
                        <p className="text-xs text-gray-500">{item.branch_code}</p>
                      </div>
                    </td>
                    <td className="p-3 text-sm text-gray-300">{item.penjaga_name}</td>
                    <td className="p-3 text-sm text-gray-400 capitalize">{item.shift}</td>
                    <td className="p-3 text-sm text-right text-gray-300">{formatRupiah(item.total_penjualan)}</td>
                    <td className="p-3 text-sm text-right text-green-400">{formatRupiah(item.total_setoran)}</td>
                    <td className={`p-3 text-sm text-right font-medium ${item.selisih < 0 ? 'text-red-400' : item.selisih > 0 ? 'text-blue-400' : 'text-gray-400'}`}>
                      {item.selisih < 0 ? '-' : item.selisih > 0 ? '+' : ''}{formatRupiah(Math.abs(item.selisih))}
                    </td>
                    <td className="p-3 text-center">{getStatusBadge(item.status, item.selisih)}</td>
                    <td className="p-3">
                      <div className="flex items-center justify-center gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => openEdit(item)}
                          className="h-8 w-8 p-0 text-gray-400 hover:text-amber-400"
                        >
                          <Edit className="h-4 w-4" />
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

      {/* Input Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-3xl bg-[#0f0a0a] border-red-900/30">
          <DialogHeader>
            <DialogTitle className="text-amber-100">
              {editData ? 'Edit Setoran' : 'Input Setoran Harian'}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-xs text-gray-400">Tanggal</label>
                <Input
                  type="date"
                  value={formData.tanggal}
                  onChange={(e) => setFormData({...formData, tanggal: e.target.value})}
                  className="bg-red-950/30 border-red-900/30"
                  required
                />
              </div>
              <div>
                <label className="text-xs text-gray-400">Jam Buka</label>
                <Input
                  type="time"
                  value={formData.jam_buka}
                  onChange={(e) => setFormData({...formData, jam_buka: e.target.value})}
                  className="bg-red-950/30 border-red-900/30"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400">Jam Tutup</label>
                <Input
                  type="time"
                  value={formData.jam_tutup}
                  onChange={(e) => setFormData({...formData, jam_tutup: e.target.value})}
                  className="bg-red-950/30 border-red-900/30"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400">Shift</label>
                <Select value={formData.shift} onValueChange={(v) => setFormData({...formData, shift: v})}>
                  <SelectTrigger className="bg-red-950/30 border-red-900/30">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pagi">Pagi</SelectItem>
                    <SelectItem value="siang">Siang</SelectItem>
                    <SelectItem value="malam">Malam</SelectItem>
                    <SelectItem value="full">Full Day</SelectItem>
                  </SelectContent>
                </Select>
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
                <label className="text-xs text-gray-400">Penjaga / Kasir</label>
                <Select value={formData.penjaga_id} onValueChange={handleEmployeeChange}>
                  <SelectTrigger className="bg-red-950/30 border-red-900/30">
                    <SelectValue placeholder="Pilih Penjaga" />
                  </SelectTrigger>
                  <SelectContent>
                    {employees.map(e => (
                      <SelectItem key={e.id} value={e.id}>{e.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="border-t border-red-900/20 pt-4">
              <h3 className="text-sm font-medium text-amber-200 mb-3">Breakdown Penjualan</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-xs text-gray-400">Cash</label>
                  <Input
                    type="number"
                    value={formData.penjualan_cash}
                    onChange={(e) => setFormData({...formData, penjualan_cash: parseFloat(e.target.value) || 0})}
                    className="bg-red-950/30 border-red-900/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Transfer Bank</label>
                  <Input
                    type="number"
                    value={formData.penjualan_transfer}
                    onChange={(e) => setFormData({...formData, penjualan_transfer: parseFloat(e.target.value) || 0})}
                    className="bg-red-950/30 border-red-900/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">E-Wallet (QRIS)</label>
                  <Input
                    type="number"
                    value={formData.penjualan_ewallet}
                    onChange={(e) => setFormData({...formData, penjualan_ewallet: parseFloat(e.target.value) || 0})}
                    className="bg-red-950/30 border-red-900/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Debit Card</label>
                  <Input
                    type="number"
                    value={formData.penjualan_debit}
                    onChange={(e) => setFormData({...formData, penjualan_debit: parseFloat(e.target.value) || 0})}
                    className="bg-red-950/30 border-red-900/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Credit Card</label>
                  <Input
                    type="number"
                    value={formData.penjualan_credit}
                    onChange={(e) => setFormData({...formData, penjualan_credit: parseFloat(e.target.value) || 0})}
                    className="bg-red-950/30 border-red-900/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Piutang</label>
                  <Input
                    type="number"
                    value={formData.penjualan_piutang}
                    onChange={(e) => setFormData({...formData, penjualan_piutang: parseFloat(e.target.value) || 0})}
                    className="bg-red-950/30 border-red-900/30"
                  />
                </div>
              </div>
              <div className="mt-3 p-3 bg-green-900/20 rounded-lg">
                <p className="text-sm text-gray-400">Total Penjualan: <span className="text-green-400 font-bold">{formatRupiah(calculateTotal())}</span></p>
              </div>
            </div>

            <div className="border-t border-red-900/20 pt-4">
              <h3 className="text-sm font-medium text-amber-200 mb-3">Setoran</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-xs text-gray-400">Jumlah Setoran Cash</label>
                  <Input
                    type="number"
                    value={formData.total_setoran}
                    onChange={(e) => setFormData({...formData, total_setoran: parseFloat(e.target.value) || 0})}
                    className="bg-red-950/30 border-red-900/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Metode Setoran</label>
                  <Select value={formData.metode_setoran} onValueChange={(v) => setFormData({...formData, metode_setoran: v})}>
                    <SelectTrigger className="bg-red-950/30 border-red-900/30">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cash">Cash</SelectItem>
                      <SelectItem value="transfer">Transfer</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs text-gray-400">Jumlah Transaksi</label>
                  <Input
                    type="number"
                    value={formData.total_transaksi}
                    onChange={(e) => setFormData({...formData, total_transaksi: parseInt(e.target.value) || 0})}
                    className="bg-red-950/30 border-red-900/30"
                  />
                </div>
              </div>
              {formData.total_setoran > 0 && (
                <div className={`mt-3 p-3 rounded-lg ${formData.total_setoran - formData.penjualan_cash < 0 ? 'bg-red-900/20' : formData.total_setoran - formData.penjualan_cash > 0 ? 'bg-blue-900/20' : 'bg-green-900/20'}`}>
                  <p className="text-sm text-gray-400">
                    Selisih: 
                    <span className={`font-bold ml-2 ${formData.total_setoran - formData.penjualan_cash < 0 ? 'text-red-400' : formData.total_setoran - formData.penjualan_cash > 0 ? 'text-blue-400' : 'text-green-400'}`}>
                      {formatRupiah(formData.total_setoran - formData.penjualan_cash)}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">(Setoran - Penjualan Cash)</span>
                  </p>
                </div>
              )}
            </div>

            <div>
              <label className="text-xs text-gray-400">Catatan</label>
              <Input
                value={formData.catatan_penjaga}
                onChange={(e) => setFormData({...formData, catatan_penjaga: e.target.value})}
                className="bg-red-950/30 border-red-900/30"
                placeholder="Catatan tambahan..."
              />
            </div>

            <DialogFooter>
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

export default SetoranHarian;
