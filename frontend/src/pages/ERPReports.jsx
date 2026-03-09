import React, { useState, useEffect } from 'react';
import { 
  FileText, Download, Calendar, Building2, Users, DollarSign,
  BarChart2, TrendingUp, AlertTriangle, Clock, Printer
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const ERPReports = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('executive');
  
  // Filters
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [tanggal, setTanggal] = useState(new Date().toISOString().split('T')[0]);
  
  // Report data
  const [executiveDaily, setExecutiveDaily] = useState(null);
  const [executiveMonthly, setExecutiveMonthly] = useState(null);
  const [setoranReport, setSetoranReport] = useState(null);
  const [selisihReport, setSelisihReport] = useState(null);
  const [attendanceReport, setAttendanceReport] = useState(null);
  const [payrollReport, setPayrollReport] = useState(null);

  useEffect(() => {
    fetchExecutiveDaily();
    fetchExecutiveMonthly();
  }, []);

  const fetchExecutiveDaily = async () => {
    try {
      const res = await api.get(`/api/reports/executive/daily?tanggal=${tanggal}`);
      setExecutiveDaily(res.data);
    } catch (err) {
      console.error('Error fetching executive daily:', err);
    }
  };

  const fetchExecutiveMonthly = async () => {
    try {
      const res = await api.get(`/api/reports/executive/monthly?month=${month}&year=${year}`);
      setExecutiveMonthly(res.data);
    } catch (err) {
      console.error('Error fetching executive monthly:', err);
    }
  };

  const fetchSetoranReport = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/api/reports/setoran/monthly?month=${month}&year=${year}`);
      setSetoranReport(res.data);
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat laporan setoran', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const fetchSelisihReport = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/api/reports/selisih/by-employee?month=${month}&year=${year}`);
      setSelisihReport(res.data);
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat laporan selisih', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const fetchAttendanceReport = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/api/reports/attendance/monthly?month=${month}&year=${year}`);
      setAttendanceReport(res.data);
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat laporan absensi', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const fetchPayrollReport = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/api/reports/payroll/summary?year=${year}`);
      setPayrollReport(res.data);
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat laporan payroll', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const formatRupiah = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  };

  const months = [
    { val: 1, label: 'Januari' }, { val: 2, label: 'Februari' }, { val: 3, label: 'Maret' },
    { val: 4, label: 'April' }, { val: 5, label: 'Mei' }, { val: 6, label: 'Juni' },
    { val: 7, label: 'Juli' }, { val: 8, label: 'Agustus' }, { val: 9, label: 'September' },
    { val: 10, label: 'Oktober' }, { val: 11, label: 'November' }, { val: 12, label: 'Desember' }
  ];

  return (
    <div className="p-6 space-y-6" data-testid="erp-reports-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Laporan ERP</h1>
          <p className="text-gray-400 text-sm">Comprehensive ERP reporting system</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={month.toString()} onValueChange={(v) => setMonth(parseInt(v))}>
            <SelectTrigger className="w-32 bg-red-950/30 border-red-900/30">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {months.map(m => (
                <SelectItem key={m.val} value={m.val.toString()}>{m.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={year.toString()} onValueChange={(v) => setYear(parseInt(v))}>
            <SelectTrigger className="w-24 bg-red-950/30 border-red-900/30">
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

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-red-950/30">
          <TabsTrigger value="executive" className="flex items-center gap-2">
            <BarChart2 className="h-4 w-4" /> Executive
          </TabsTrigger>
          <TabsTrigger value="setoran" onClick={fetchSetoranReport} className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" /> Setoran
          </TabsTrigger>
          <TabsTrigger value="selisih" onClick={fetchSelisihReport} className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" /> Selisih Kas
          </TabsTrigger>
          <TabsTrigger value="attendance" onClick={fetchAttendanceReport} className="flex items-center gap-2">
            <Clock className="h-4 w-4" /> Absensi
          </TabsTrigger>
          <TabsTrigger value="payroll" onClick={fetchPayrollReport} className="flex items-center gap-2">
            <Users className="h-4 w-4" /> Payroll
          </TabsTrigger>
        </TabsList>

        {/* Executive Summary Tab */}
        <TabsContent value="executive" className="mt-4 space-y-6">
          {executiveDaily && (
            <Card className="bg-[#0f0a0a] border-red-900/20">
              <CardHeader>
                <CardTitle className="text-lg text-amber-200">Summary Hari Ini - {executiveDaily.tanggal}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-blue-900/20 rounded-lg">
                    <p className="text-xs text-gray-400">Cabang Setor</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {executiveDaily.operasional?.sudah_setor}/{executiveDaily.operasional?.total_cabang}
                    </p>
                  </div>
                  <div className="p-4 bg-green-900/20 rounded-lg">
                    <p className="text-xs text-gray-400">Total Penjualan</p>
                    <p className="text-2xl font-bold text-green-400">{formatRupiah(executiveDaily.operasional?.total_penjualan)}</p>
                  </div>
                  <div className="p-4 bg-red-900/20 rounded-lg">
                    <p className="text-xs text-gray-400">Total Minus</p>
                    <p className="text-2xl font-bold text-red-400">{formatRupiah(executiveDaily.operasional?.total_minus)}</p>
                  </div>
                  <div className="p-4 bg-purple-900/20 rounded-lg">
                    <p className="text-xs text-gray-400">Kehadiran</p>
                    <p className="text-2xl font-bold text-purple-400">
                      {executiveDaily.kehadiran?.hadir}/{executiveDaily.kehadiran?.total_karyawan}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {executiveMonthly && (
            <Card className="bg-[#0f0a0a] border-red-900/20">
              <CardHeader>
                <CardTitle className="text-lg text-amber-200">Summary Bulan {months[month-1]?.label} {year}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-gradient-to-br from-green-900/30 to-green-800/20 rounded-lg border border-green-700/30">
                    <p className="text-xs text-gray-400 mb-2">Penjualan</p>
                    <p className="text-xl font-bold text-green-400">{formatRupiah(executiveMonthly.penjualan?.total)}</p>
                    <p className="text-xs text-gray-500">{executiveMonthly.penjualan?.total_transaksi} transaksi</p>
                  </div>
                  <div className="p-4 bg-gradient-to-br from-red-900/30 to-red-800/20 rounded-lg border border-red-700/30">
                    <p className="text-xs text-gray-400 mb-2">Selisih Kas</p>
                    <p className="text-xl font-bold text-red-400">{formatRupiah(executiveMonthly.selisih_kas?.total_minus)}</p>
                    <p className="text-xs text-gray-500">{executiveMonthly.selisih_kas?.pending_count} pending</p>
                  </div>
                  <div className="p-4 bg-gradient-to-br from-blue-900/30 to-blue-800/20 rounded-lg border border-blue-700/30">
                    <p className="text-xs text-gray-400 mb-2">Kehadiran</p>
                    <p className="text-xl font-bold text-blue-400">{executiveMonthly.kehadiran?.total_hadir}</p>
                    <p className="text-xs text-gray-500">{executiveMonthly.kehadiran?.total_telat} telat</p>
                  </div>
                  <div className="p-4 bg-gradient-to-br from-amber-900/30 to-amber-800/20 rounded-lg border border-amber-700/30">
                    <p className="text-xs text-gray-400 mb-2">Payroll</p>
                    <p className="text-xl font-bold text-amber-400">{formatRupiah(executiveMonthly.payroll?.total_net)}</p>
                    <p className="text-xs text-gray-500">{executiveMonthly.payroll?.employee_count} karyawan</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Setoran Tab */}
        <TabsContent value="setoran" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-amber-200">Laporan Setoran {months[month-1]?.label} {year}</CardTitle>
              <Button variant="outline" size="sm" className="border-amber-700/30">
                <Download className="h-4 w-4 mr-1" /> Export
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-center text-gray-400 py-8">Loading...</p>
              ) : setoranReport ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="p-3 bg-green-900/20 rounded-lg text-center">
                      <p className="text-xs text-gray-400">Total Penjualan</p>
                      <p className="text-lg font-bold text-green-400">{formatRupiah(setoranReport.total_penjualan)}</p>
                    </div>
                    <div className="p-3 bg-blue-900/20 rounded-lg text-center">
                      <p className="text-xs text-gray-400">Total Setoran</p>
                      <p className="text-lg font-bold text-blue-400">{formatRupiah(setoranReport.total_setoran)}</p>
                    </div>
                    <div className="p-3 bg-red-900/20 rounded-lg text-center">
                      <p className="text-xs text-gray-400">Total Minus</p>
                      <p className="text-lg font-bold text-red-400">{formatRupiah(setoranReport.total_minus)}</p>
                    </div>
                    <div className="p-3 bg-cyan-900/20 rounded-lg text-center">
                      <p className="text-xs text-gray-400">Total Plus</p>
                      <p className="text-lg font-bold text-cyan-400">{formatRupiah(setoranReport.total_plus)}</p>
                    </div>
                  </div>
                  <h4 className="text-sm font-medium text-gray-300">By Branch</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-red-950/30">
                        <tr className="text-left text-xs text-gray-400">
                          <th className="p-2">Cabang</th>
                          <th className="p-2 text-right">Penjualan</th>
                          <th className="p-2 text-right">Setoran</th>
                          <th className="p-2 text-right">Minus</th>
                          <th className="p-2 text-right">Plus</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-red-900/20">
                        {setoranReport.by_branch?.slice(0, 10).map((b, idx) => (
                          <tr key={idx}>
                            <td className="p-2 text-amber-200">{b.branch_name}</td>
                            <td className="p-2 text-right text-green-400">{formatRupiah(b.total_penjualan)}</td>
                            <td className="p-2 text-right text-blue-400">{formatRupiah(b.total_setoran)}</td>
                            <td className="p-2 text-right text-red-400">{formatRupiah(b.total_minus)}</td>
                            <td className="p-2 text-right text-cyan-400">{formatRupiah(b.total_plus)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <p className="text-center text-gray-400 py-8">Klik tab untuk memuat data</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Selisih Tab */}
        <TabsContent value="selisih" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-amber-200">Laporan Selisih Kas by Karyawan</CardTitle>
              <Button variant="outline" size="sm" className="border-amber-700/30">
                <Download className="h-4 w-4 mr-1" /> Export
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-center text-gray-400 py-8">Loading...</p>
              ) : selisihReport ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="p-3 bg-red-900/20 rounded-lg text-center">
                      <p className="text-xs text-gray-400">Total Minus</p>
                      <p className="text-2xl font-bold text-red-400">{formatRupiah(selisihReport.total_minus)}</p>
                    </div>
                    <div className="p-3 bg-cyan-900/20 rounded-lg text-center">
                      <p className="text-xs text-gray-400">Total Plus</p>
                      <p className="text-2xl font-bold text-cyan-400">{formatRupiah(selisihReport.total_plus)}</p>
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-red-950/30">
                        <tr className="text-left text-xs text-gray-400">
                          <th className="p-2">Karyawan</th>
                          <th className="p-2 text-center">Minus</th>
                          <th className="p-2 text-center">Plus</th>
                          <th className="p-2 text-right">Total Minus</th>
                          <th className="p-2 text-right">Total Plus</th>
                          <th className="p-2 text-center">Pending</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-red-900/20">
                        {selisihReport.employees?.map((e, idx) => (
                          <tr key={idx}>
                            <td className="p-2 text-amber-200">{e.employee_name}</td>
                            <td className="p-2 text-center text-red-400">{e.minus_count}x</td>
                            <td className="p-2 text-center text-cyan-400">{e.plus_count}x</td>
                            <td className="p-2 text-right text-red-400">{formatRupiah(e.total_minus)}</td>
                            <td className="p-2 text-right text-cyan-400">{formatRupiah(e.total_plus)}</td>
                            <td className="p-2 text-center text-yellow-400">{e.pending_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <p className="text-center text-gray-400 py-8">Klik tab untuk memuat data</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Attendance Tab */}
        <TabsContent value="attendance" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-amber-200">Laporan Absensi {months[month-1]?.label} {year}</CardTitle>
              <Button variant="outline" size="sm" className="border-amber-700/30">
                <Download className="h-4 w-4 mr-1" /> Export
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-center text-gray-400 py-8">Loading...</p>
              ) : attendanceReport ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-6 gap-3 mb-6">
                    <div className="p-2 bg-green-900/20 rounded-lg text-center">
                      <p className="text-[10px] text-gray-400">Total Hadir</p>
                      <p className="text-lg font-bold text-green-400">{attendanceReport.summary?.total_hadir}</p>
                    </div>
                    <div className="p-2 bg-yellow-900/20 rounded-lg text-center">
                      <p className="text-[10px] text-gray-400">Telat</p>
                      <p className="text-lg font-bold text-yellow-400">{attendanceReport.summary?.total_telat}</p>
                    </div>
                    <div className="p-2 bg-red-900/20 rounded-lg text-center">
                      <p className="text-[10px] text-gray-400">Alpha</p>
                      <p className="text-lg font-bold text-red-400">{attendanceReport.summary?.total_alpha}</p>
                    </div>
                    <div className="p-2 bg-blue-900/20 rounded-lg text-center">
                      <p className="text-[10px] text-gray-400">Izin</p>
                      <p className="text-lg font-bold text-blue-400">{attendanceReport.summary?.total_izin}</p>
                    </div>
                    <div className="p-2 bg-purple-900/20 rounded-lg text-center">
                      <p className="text-[10px] text-gray-400">Cuti</p>
                      <p className="text-lg font-bold text-purple-400">{attendanceReport.summary?.total_cuti}</p>
                    </div>
                    <div className="p-2 bg-orange-900/20 rounded-lg text-center">
                      <p className="text-[10px] text-gray-400">Sakit</p>
                      <p className="text-lg font-bold text-orange-400">{attendanceReport.summary?.total_sakit}</p>
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-red-950/30">
                        <tr className="text-left text-xs text-gray-400">
                          <th className="p-2">Karyawan</th>
                          <th className="p-2">NIK</th>
                          <th className="p-2 text-center">Hadir</th>
                          <th className="p-2 text-center">Telat</th>
                          <th className="p-2 text-center">Alpha</th>
                          <th className="p-2 text-center">Izin</th>
                          <th className="p-2 text-right">Jam Kerja</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-red-900/20">
                        {attendanceReport.employees?.slice(0, 20).map((e, idx) => (
                          <tr key={idx}>
                            <td className="p-2 text-amber-200">{e.employee_name}</td>
                            <td className="p-2 text-gray-400 font-mono text-xs">{e.employee_nik}</td>
                            <td className="p-2 text-center text-green-400">{e.hadir}</td>
                            <td className="p-2 text-center text-yellow-400">{e.telat}</td>
                            <td className="p-2 text-center text-red-400">{e.alpha}</td>
                            <td className="p-2 text-center text-blue-400">{e.izin + e.cuti + e.sakit}</td>
                            <td className="p-2 text-right text-gray-300">{e.total_jam_kerja?.toFixed(1)} jam</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <p className="text-center text-gray-400 py-8">Klik tab untuk memuat data</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Payroll Tab */}
        <TabsContent value="payroll" className="mt-4">
          <Card className="bg-[#0f0a0a] border-red-900/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-amber-200">Laporan Payroll Tahun {year}</CardTitle>
              <Button variant="outline" size="sm" className="border-amber-700/30">
                <Download className="h-4 w-4 mr-1" /> Export
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-center text-gray-400 py-8">Loading...</p>
              ) : payrollReport ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="p-3 bg-green-900/20 rounded-lg text-center">
                      <p className="text-xs text-gray-400">Total Bruto</p>
                      <p className="text-xl font-bold text-green-400">{formatRupiah(payrollReport.total_gross)}</p>
                    </div>
                    <div className="p-3 bg-red-900/20 rounded-lg text-center">
                      <p className="text-xs text-gray-400">Total Potongan</p>
                      <p className="text-xl font-bold text-red-400">{formatRupiah(payrollReport.total_deductions)}</p>
                    </div>
                    <div className="p-3 bg-amber-900/20 rounded-lg text-center">
                      <p className="text-xs text-gray-400">Total Netto</p>
                      <p className="text-xl font-bold text-amber-400">{formatRupiah(payrollReport.total_net)}</p>
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-red-950/30">
                        <tr className="text-left text-xs text-gray-400">
                          <th className="p-2">Periode</th>
                          <th className="p-2 text-center">Karyawan</th>
                          <th className="p-2 text-right">Total Bruto</th>
                          <th className="p-2 text-right">Potongan</th>
                          <th className="p-2 text-right">Total Netto</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-red-900/20">
                        {payrollReport.monthly?.map((m, idx) => (
                          <tr key={idx}>
                            <td className="p-2 text-amber-200">{m.period}</td>
                            <td className="p-2 text-center text-gray-300">{m.employee_count}</td>
                            <td className="p-2 text-right text-green-400">{formatRupiah(m.total_gross)}</td>
                            <td className="p-2 text-right text-red-400">{formatRupiah(m.total_deductions)}</td>
                            <td className="p-2 text-right text-amber-400">{formatRupiah(m.total_net)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <p className="text-center text-gray-400 py-8">Klik tab untuk memuat data</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ERPReports;
