import React, { useState, useEffect } from 'react';
import { 
  BadgeDollarSign, Plus, Calendar, Building2, Users, CheckCircle,
  DollarSign, Clock, AlertTriangle, FileText, Download, Printer
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const Payroll = () => {
  const { toast } = useToast();
  const [periods, setPeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [details, setDetails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  
  // Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newMonth, setNewMonth] = useState(new Date().getMonth() + 1);
  const [newYear, setNewYear] = useState(new Date().getFullYear());
  
  // Detail Modal
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedDetail, setSelectedDetail] = useState(null);

  useEffect(() => {
    fetchPeriods();
  }, []);

  const fetchPeriods = async () => {
    try {
      setLoading(true);
      const res = await api.get('/api/payroll/periods');
      setPeriods(res.data.periods || []);
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat data periode', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const fetchPeriodDetails = async (periodId) => {
    try {
      setLoadingDetails(true);
      const res = await api.get(`/api/payroll/periods/${periodId}`);
      setSelectedPeriod(res.data.period);
      setDetails(res.data.details || []);
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat detail payroll', variant: 'destructive' });
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleCreatePeriod = async () => {
    try {
      await api.post('/api/payroll/periods', {
        period_month: newMonth,
        period_year: newYear
      });
      toast({ title: 'Sukses', description: 'Periode payroll berhasil dibuat' });
      setShowCreateModal(false);
      fetchPeriods();
    } catch (err) {
      toast({ 
        title: 'Error', 
        description: err.response?.data?.detail || 'Gagal membuat periode', 
        variant: 'destructive' 
      });
    }
  };

  const handleGeneratePayroll = async (periodId) => {
    try {
      toast({ title: 'Info', description: 'Generating payroll...' });
      const res = await api.post(`/api/payroll/periods/${periodId}/generate`);
      toast({ 
        title: 'Sukses', 
        description: `Payroll berhasil digenerate untuk ${res.data.total_employees} karyawan`
      });
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (err) {
      toast({ 
        title: 'Error', 
        description: err.response?.data?.detail || 'Gagal generate payroll', 
        variant: 'destructive' 
      });
    }
  };

  const handleApprove = async (periodId) => {
    try {
      await api.post(`/api/payroll/periods/${periodId}/approve`, null, {
        params: { approved_by: 'Admin' }
      });
      toast({ title: 'Sukses', description: 'Payroll berhasil diapprove' });
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (err) {
      toast({ 
        title: 'Error', 
        description: err.response?.data?.detail || 'Gagal approve payroll', 
        variant: 'destructive' 
      });
    }
  };

  const handlePay = async (periodId) => {
    if (!window.confirm('Tandai payroll sebagai sudah dibayar?')) return;
    try {
      await api.post(`/api/payroll/periods/${periodId}/pay`);
      toast({ title: 'Sukses', description: 'Payroll ditandai sudah dibayar' });
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (err) {
      toast({ 
        title: 'Error', 
        description: err.response?.data?.detail || 'Gagal update status', 
        variant: 'destructive' 
      });
    }
  };

  const openDetail = (detail) => {
    setSelectedDetail(detail);
    setShowDetailModal(true);
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: { bg: 'bg-gray-500/20', text: 'text-gray-400', label: 'Draft' },
      processing: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Processing' },
      approved: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Approved' },
      paid: { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Paid' }
    };
    const badge = badges[status] || badges.draft;
    return <span className={`px-2 py-1 text-xs rounded-full ${badge.bg} ${badge.text}`}>{badge.label}</span>;
  };

  const formatRupiah = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  };

  return (
    <div className="p-6 space-y-6" data-testid="payroll-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Payroll</h1>
          <p className="text-gray-400 text-sm">Penggajian terintegrasi dengan absensi dan selisih kas</p>
        </div>
        <Button 
          onClick={() => setShowCreateModal(true)}
          className="bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-700 hover:to-amber-700"
          data-testid="btn-buat-periode"
        >
          <Plus className="h-4 w-4 mr-2" /> Buat Periode Baru
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Period List */}
        <Card className="bg-[#0f0a0a] border-red-900/20">
          <CardHeader>
            <CardTitle className="text-lg text-amber-200">Periode Payroll</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[600px] overflow-y-auto">
            {loading ? (
              <p className="text-gray-400 text-center py-4">Loading...</p>
            ) : periods.length === 0 ? (
              <p className="text-gray-400 text-center py-4">Belum ada periode</p>
            ) : periods.map((period) => (
              <div
                key={period.id}
                onClick={() => fetchPeriodDetails(period.id)}
                className={`p-3 rounded-lg cursor-pointer transition-all ${
                  selectedPeriod?.id === period.id
                    ? 'bg-red-900/30 border border-red-700/30'
                    : 'bg-red-950/20 hover:bg-red-950/40'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <p className="font-medium text-amber-200">{period.period_name}</p>
                  {getStatusBadge(period.status)}
                </div>
                <div className="text-xs text-gray-400 space-y-1">
                  <p>Karyawan: {period.total_employees || 0}</p>
                  <p>Total: {formatRupiah(period.total_net)}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Period Details */}
        <div className="lg:col-span-2 space-y-4">
          {selectedPeriod ? (
            <>
              {/* Period Info */}
              <Card className="bg-[#0f0a0a] border-red-900/20">
                <CardContent className="p-4">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                      <h2 className="text-xl font-bold text-amber-200">{selectedPeriod.period_name}</h2>
                      <p className="text-sm text-gray-400">
                        {selectedPeriod.start_date} s/d {selectedPeriod.end_date}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {selectedPeriod.status === 'draft' && (
                        <Button
                          onClick={() => handleGeneratePayroll(selectedPeriod.id)}
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          Generate Payroll
                        </Button>
                      )}
                      {selectedPeriod.status === 'draft' && details.length > 0 && (
                        <Button
                          onClick={() => handleApprove(selectedPeriod.id)}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          Approve
                        </Button>
                      )}
                      {selectedPeriod.status === 'approved' && (
                        <Button
                          onClick={() => handlePay(selectedPeriod.id)}
                          className="bg-amber-600 hover:bg-amber-700"
                        >
                          Tandai Dibayar
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border-blue-700/30">
                  <CardContent className="p-4 text-center">
                    <Users className="h-5 w-5 text-blue-400 mx-auto mb-1" />
                    <p className="text-xl font-bold text-blue-400">{selectedPeriod.total_employees}</p>
                    <p className="text-xs text-gray-400">Karyawan</p>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-green-900/30 to-green-800/20 border-green-700/30">
                  <CardContent className="p-4 text-center">
                    <DollarSign className="h-5 w-5 text-green-400 mx-auto mb-1" />
                    <p className="text-lg font-bold text-green-400">{formatRupiah(selectedPeriod.total_gross)}</p>
                    <p className="text-xs text-gray-400">Total Bruto</p>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-red-900/30 to-red-800/20 border-red-700/30">
                  <CardContent className="p-4 text-center">
                    <AlertTriangle className="h-5 w-5 text-red-400 mx-auto mb-1" />
                    <p className="text-lg font-bold text-red-400">{formatRupiah(selectedPeriod.total_deductions)}</p>
                    <p className="text-xs text-gray-400">Total Potongan</p>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-amber-900/30 to-amber-800/20 border-amber-700/30">
                  <CardContent className="p-4 text-center">
                    <BadgeDollarSign className="h-5 w-5 text-amber-400 mx-auto mb-1" />
                    <p className="text-lg font-bold text-amber-400">{formatRupiah(selectedPeriod.total_net)}</p>
                    <p className="text-xs text-gray-400">Total Netto</p>
                  </CardContent>
                </Card>
              </div>

              {/* Details Table */}
              <Card className="bg-[#0f0a0a] border-red-900/20">
                <CardHeader>
                  <CardTitle className="text-lg text-amber-200">Detail Penggajian</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-red-950/30">
                        <tr className="text-left text-xs text-gray-400">
                          <th className="p-3">Karyawan</th>
                          <th className="p-3">Jabatan</th>
                          <th className="p-3 text-center">Hadir</th>
                          <th className="p-3 text-center">Telat</th>
                          <th className="p-3 text-right">Gaji Pokok</th>
                          <th className="p-3 text-right">Potongan</th>
                          <th className="p-3 text-right">Take Home</th>
                          <th className="p-3 text-center">Aksi</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-red-900/20">
                        {loadingDetails ? (
                          <tr>
                            <td colSpan="8" className="p-8 text-center text-gray-400">Loading...</td>
                          </tr>
                        ) : details.length === 0 ? (
                          <tr>
                            <td colSpan="8" className="p-8 text-center text-gray-400">
                              Belum ada data. Klik "Generate Payroll" untuk memproses.
                            </td>
                          </tr>
                        ) : details.map((detail) => (
                          <tr key={detail.id} className="hover:bg-red-950/20">
                            <td className="p-3">
                              <div>
                                <p className="text-sm font-medium text-amber-200">{detail.employee_name}</p>
                                <p className="text-xs text-gray-500">{detail.employee_nik}</p>
                              </div>
                            </td>
                            <td className="p-3 text-sm text-gray-300">{detail.jabatan}</td>
                            <td className="p-3 text-center">
                              <span className="text-green-400">{detail.hari_hadir}</span>
                              <span className="text-gray-500">/{detail.hari_kerja}</span>
                            </td>
                            <td className="p-3 text-center">
                              {detail.hari_telat > 0 ? (
                                <span className="text-yellow-400">{detail.hari_telat}x</span>
                              ) : (
                                <span className="text-gray-500">-</span>
                              )}
                            </td>
                            <td className="p-3 text-right text-sm text-gray-300">{formatRupiah(detail.gaji_pokok)}</td>
                            <td className="p-3 text-right text-sm text-red-400">{formatRupiah(detail.total_deductions)}</td>
                            <td className="p-3 text-right text-sm font-bold text-green-400">{formatRupiah(detail.take_home_pay)}</td>
                            <td className="p-3 text-center">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openDetail(detail)}
                                className="text-gray-400 hover:text-amber-400"
                              >
                                <FileText className="h-4 w-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="bg-[#0f0a0a] border-red-900/20">
              <CardContent className="p-8 text-center text-gray-400">
                Pilih periode payroll untuk melihat detail
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Create Period Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="bg-[#0f0a0a] border-red-900/30">
          <DialogHeader>
            <DialogTitle className="text-amber-100">Buat Periode Payroll Baru</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400">Bulan</label>
                <Select value={newMonth.toString()} onValueChange={(v) => setNewMonth(parseInt(v))}>
                  <SelectTrigger className="bg-red-950/30 border-red-900/30">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[
                      { val: 1, label: 'Januari' },
                      { val: 2, label: 'Februari' },
                      { val: 3, label: 'Maret' },
                      { val: 4, label: 'April' },
                      { val: 5, label: 'Mei' },
                      { val: 6, label: 'Juni' },
                      { val: 7, label: 'Juli' },
                      { val: 8, label: 'Agustus' },
                      { val: 9, label: 'September' },
                      { val: 10, label: 'Oktober' },
                      { val: 11, label: 'November' },
                      { val: 12, label: 'Desember' }
                    ].map(m => (
                      <SelectItem key={m.val} value={m.val.toString()}>{m.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs text-gray-400">Tahun</label>
                <Select value={newYear.toString()} onValueChange={(v) => setNewYear(parseInt(v))}>
                  <SelectTrigger className="bg-red-950/30 border-red-900/30">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[2024, 2025, 2026, 2027].map(y => (
                      <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>Batal</Button>
            <Button onClick={handleCreatePeriod} className="bg-gradient-to-r from-red-600 to-amber-600">
              Buat Periode
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="max-w-2xl bg-[#0f0a0a] border-red-900/30">
          <DialogHeader>
            <DialogTitle className="text-amber-100">Slip Gaji</DialogTitle>
          </DialogHeader>
          {selectedDetail && (
            <div className="space-y-4">
              <div className="p-4 bg-red-950/30 rounded-lg">
                <h3 className="font-bold text-amber-200">{selectedDetail.employee_name}</h3>
                <p className="text-sm text-gray-400">{selectedDetail.employee_nik} | {selectedDetail.jabatan}</p>
                <p className="text-sm text-gray-400">{selectedDetail.branch_name}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-green-400 mb-2">Pendapatan</h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Gaji Pokok</span>
                      <span className="text-gray-200">{formatRupiah(selectedDetail.gaji_pokok)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Tunj. Jabatan</span>
                      <span className="text-gray-200">{formatRupiah(selectedDetail.tunjangan_jabatan)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Tunj. Transport</span>
                      <span className="text-gray-200">{formatRupiah(selectedDetail.tunjangan_transport)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Tunj. Makan</span>
                      <span className="text-gray-200">{formatRupiah(selectedDetail.tunjangan_makan)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Bonus Kehadiran</span>
                      <span className="text-gray-200">{formatRupiah(selectedDetail.bonus_kehadiran)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Lembur</span>
                      <span className="text-gray-200">{formatRupiah(selectedDetail.lembur_nominal)}</span>
                    </div>
                    <div className="flex justify-between border-t border-green-700/30 pt-1 mt-1">
                      <span className="text-green-400 font-medium">Total Pendapatan</span>
                      <span className="text-green-400 font-bold">{formatRupiah(selectedDetail.total_earnings)}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-red-400 mb-2">Potongan</h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Pot. Telat</span>
                      <span className="text-gray-200">{formatRupiah(selectedDetail.potongan_telat)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Pot. Alpha</span>
                      <span className="text-gray-200">{formatRupiah(selectedDetail.potongan_alpha)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Pot. Minus Kas</span>
                      <span className="text-gray-200">{formatRupiah(selectedDetail.potongan_minus_kas)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Pot. Pinjaman</span>
                      <span className="text-gray-200">{formatRupiah(selectedDetail.potongan_pinjaman)}</span>
                    </div>
                    <div className="flex justify-between border-t border-red-700/30 pt-1 mt-1">
                      <span className="text-red-400 font-medium">Total Potongan</span>
                      <span className="text-red-400 font-bold">{formatRupiah(selectedDetail.total_deductions)}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-green-900/20 rounded-lg border border-green-700/30">
                <div className="flex justify-between items-center">
                  <span className="text-lg text-gray-300">Take Home Pay</span>
                  <span className="text-2xl font-bold text-green-400">{formatRupiah(selectedDetail.take_home_pay)}</span>
                </div>
              </div>

              <div className="p-3 bg-red-950/20 rounded-lg">
                <h4 className="text-xs text-gray-400 mb-2">Rekap Kehadiran</h4>
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  <div>
                    <p className="text-green-400 font-bold">{selectedDetail.hari_hadir}</p>
                    <p className="text-gray-500">Hadir</p>
                  </div>
                  <div>
                    <p className="text-yellow-400 font-bold">{selectedDetail.hari_telat}</p>
                    <p className="text-gray-500">Telat</p>
                  </div>
                  <div>
                    <p className="text-red-400 font-bold">{selectedDetail.hari_alpha}</p>
                    <p className="text-gray-500">Alpha</p>
                  </div>
                  <div>
                    <p className="text-blue-400 font-bold">{selectedDetail.hari_izin + selectedDetail.hari_cuti + selectedDetail.hari_sakit}</p>
                    <p className="text-gray-500">Izin/Cuti</p>
                  </div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailModal(false)}>Tutup</Button>
            <Button className="bg-gradient-to-r from-red-600 to-amber-600">
              <Printer className="h-4 w-4 mr-2" /> Cetak Slip
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Payroll;
