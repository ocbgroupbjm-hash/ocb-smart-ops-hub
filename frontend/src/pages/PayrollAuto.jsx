import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Input } from '../components/ui/input';
import { FileText, Download, Calculator, Users, Building, DollarSign, RefreshCw, CheckCircle, Clock, AlertTriangle, Printer, FileSpreadsheet } from 'lucide-react';

export default function PayrollAuto() {
  const [loading, setLoading] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('all');
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [payrollResults, setPayrollResults] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [employeePayroll, setEmployeePayroll] = useState(null);
  const [summary, setSummary] = useState(null);
  const [generating, setGenerating] = useState(false);

  const months = [
    { value: 1, label: 'Januari' }, { value: 2, label: 'Februari' }, { value: 3, label: 'Maret' },
    { value: 4, label: 'April' }, { value: 5, label: 'Mei' }, { value: 6, label: 'Juni' },
    { value: 7, label: 'Juli' }, { value: 8, label: 'Agustus' }, { value: 9, label: 'September' },
    { value: 10, label: 'Oktober' }, { value: 11, label: 'November' }, { value: 12, label: 'Desember' }
  ];

  useEffect(() => {
    loadBranches();
    loadEmployees();
  }, []);

  const loadBranches = async () => {
    try {
      const res = await api.get('/api/global-map/branches');
      setBranches(res.data.branches || []);
    } catch (err) {
      console.error('Error loading branches:', err);
    }
  };

  const loadEmployees = async () => {
    try {
      const res = await api.get('/api/erp/employees');
      setEmployees(res.data.employees || []);
    } catch (err) {
      console.error('Error loading employees:', err);
    }
  };

  const calculateAllPayroll = async () => {
    setLoading(true);
    try {
      let url = `/api/payroll-auto/calculate-all?month=${selectedMonth}&year=${selectedYear}`;
      if (selectedBranch !== 'all') {
        url = `/api/payroll-auto/calculate-branch/${selectedBranch}?month=${selectedMonth}&year=${selectedYear}`;
      }
      const res = await api.get(url);
      setPayrollResults(res.data.employees || []);
      setSummary(res.data.summary);
    } catch (err) {
      console.error('Error calculating payroll:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateEmployeePayroll = async (employeeId) => {
    try {
      const res = await api.get(`/api/payroll-auto/calculate/${employeeId}?month=${selectedMonth}&year=${selectedYear}`);
      setEmployeePayroll(res.data);
      setSelectedEmployee(employeeId);
    } catch (err) {
      console.error('Error calculating employee payroll:', err);
    }
  };

  const generatePayslip = async (employeeId, format) => {
    setGenerating(true);
    try {
      const url = `/api/payroll-files/payslip/${employeeId}?period_month=${selectedMonth}&period_year=${selectedYear}&format=${format}`;
      
      if (format === 'json') {
        const res = await api.get(url);
        alert('Payslip JSON:\n' + JSON.stringify(res.data, null, 2));
      } else {
        // Download file
        const response = await api.get(url, { responseType: 'blob' });
        const blob = new Blob([response.data]);
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `payslip_${employeeId}_${selectedMonth}_${selectedYear}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(downloadUrl);
      }
    } catch (err) {
      console.error('Error generating payslip:', err);
      alert('Gagal generate payslip: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(false);
    }
  };

  const generateBranchReport = async (format) => {
    if (selectedBranch === 'all') {
      alert('Pilih cabang terlebih dahulu');
      return;
    }
    setGenerating(true);
    try {
      const url = `/api/payroll-files/report/branch/${selectedBranch}?period_month=${selectedMonth}&period_year=${selectedYear}&format=${format}`;
      
      if (format === 'json') {
        const res = await api.get(url);
        console.log('Branch Report:', res.data);
        alert('Lihat console untuk data JSON');
      } else {
        const response = await api.get(url, { responseType: 'blob' });
        const blob = new Blob([response.data]);
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `payroll_report_${selectedMonth}_${selectedYear}.${format === 'excel' ? 'xlsx' : 'csv'}`;
        document.body.appendChild(link);
        link.click();
        link.remove();
      }
    } catch (err) {
      console.error('Error generating report:', err);
    } finally {
      setGenerating(false);
    }
  };

  const formatRupiah = (num) => {
    if (num === undefined || num === null) return 'Rp 0';
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(num);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-6" data-testid="payroll-auto-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Calculator className="w-8 h-8 text-green-400" />
            Payroll Otomatis
          </h1>
          <p className="text-slate-400 mt-1">Kalkulasi gaji otomatis dari absensi & penjualan</p>
        </div>
        
        <div className="flex gap-3 flex-wrap">
          <Select value={String(selectedMonth)} onValueChange={(v) => setSelectedMonth(parseInt(v))}>
            <SelectTrigger className="w-36 bg-slate-800 border-slate-700 text-white" data-testid="month-select">
              <SelectValue placeholder="Bulan" />
            </SelectTrigger>
            <SelectContent>
              {months.map(m => (
                <SelectItem key={m.value} value={String(m.value)}>{m.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select value={String(selectedYear)} onValueChange={(v) => setSelectedYear(parseInt(v))}>
            <SelectTrigger className="w-28 bg-slate-800 border-slate-700 text-white" data-testid="year-select">
              <SelectValue placeholder="Tahun" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2025">2025</SelectItem>
              <SelectItem value="2026">2026</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={selectedBranch} onValueChange={setSelectedBranch}>
            <SelectTrigger className="w-48 bg-slate-800 border-slate-700 text-white" data-testid="branch-select">
              <SelectValue placeholder="Semua Cabang" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Semua Cabang</SelectItem>
              {branches.map(b => (
                <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Button onClick={calculateAllPayroll} disabled={loading} className="bg-green-600 hover:bg-green-700" data-testid="calculate-btn">
            <Calculator className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Hitung Payroll
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card className="bg-gradient-to-r from-blue-600 to-blue-700 border-0">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <Users className="w-10 h-10 text-blue-200 opacity-80" />
                <div className="text-right">
                  <div className="text-3xl font-bold text-white">{payrollResults.length}</div>
                  <div className="text-blue-200 text-sm">Total Karyawan</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-r from-purple-600 to-purple-700 border-0">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <DollarSign className="w-10 h-10 text-purple-200 opacity-80" />
                <div className="text-right">
                  <div className="text-2xl font-bold text-white">{formatRupiah(summary.total_gross)}</div>
                  <div className="text-purple-200 text-sm">Total Gross</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-r from-green-600 to-green-700 border-0">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <CheckCircle className="w-10 h-10 text-green-200 opacity-80" />
                <div className="text-right">
                  <div className="text-2xl font-bold text-white">{formatRupiah(summary.total_take_home_pay)}</div>
                  <div className="text-green-200 text-sm">Total Take Home Pay</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Employee List */}
        <div className="lg:col-span-2">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-400" />
                Hasil Payroll
              </CardTitle>
              {selectedBranch !== 'all' && (
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => generateBranchReport('excel')} disabled={generating} className="border-slate-600 text-slate-300 hover:text-white">
                    <FileSpreadsheet className="w-4 h-4 mr-1" /> Excel
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => generateBranchReport('csv')} disabled={generating} className="border-slate-600 text-slate-300 hover:text-white">
                    <Download className="w-4 h-4 mr-1" /> CSV
                  </Button>
                </div>
              )}
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left p-3 text-slate-400">Karyawan</th>
                      <th className="text-right p-3 text-slate-400">Hadir</th>
                      <th className="text-right p-3 text-slate-400">Alpha</th>
                      <th className="text-right p-3 text-slate-400">Telat</th>
                      <th className="text-right p-3 text-slate-400">Gross</th>
                      <th className="text-right p-3 text-slate-400">Potongan</th>
                      <th className="text-right p-3 text-slate-400">THP</th>
                      <th className="text-center p-3 text-slate-400">Aksi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr>
                        <td colSpan={8} className="text-center py-8 text-slate-400">Memuat data...</td>
                      </tr>
                    ) : payrollResults.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="text-center py-8 text-slate-400">
                          Klik "Hitung Payroll" untuk memulai kalkulasi
                        </td>
                      </tr>
                    ) : (
                      payrollResults.map((p, idx) => (
                        <tr 
                          key={p.employee?.id || idx} 
                          className={`border-b border-slate-700/50 hover:bg-slate-700/30 cursor-pointer ${
                            selectedEmployee === p.employee?.id ? 'bg-blue-900/30' : ''
                          }`}
                          onClick={() => calculateEmployeePayroll(p.employee?.id)}
                          data-testid={`payroll-row-${idx}`}
                        >
                          <td className="p-3">
                            <div className="text-white font-medium">{p.employee?.name || 'N/A'}</div>
                            <div className="text-xs text-slate-500">{p.employee?.jabatan}</div>
                          </td>
                          <td className="text-right p-3 text-green-400">{p.attendance?.total_hadir || 0}</td>
                          <td className="text-right p-3 text-red-400">{p.attendance?.total_alpha || 0}</td>
                          <td className="text-right p-3 text-yellow-400">{p.attendance?.total_telat_menit || 0}m</td>
                          <td className="text-right p-3 text-white">{formatRupiah(p.calculation?.gross)}</td>
                          <td className="text-right p-3 text-red-400">{formatRupiah(p.calculation?.potongan?.total)}</td>
                          <td className="text-right p-3 text-green-400 font-bold">{formatRupiah(p.calculation?.take_home_pay)}</td>
                          <td className="text-center p-3">
                            <div className="flex gap-1 justify-center">
                              <Button 
                                size="sm" 
                                variant="ghost" 
                                onClick={(e) => { e.stopPropagation(); generatePayslip(p.employee?.id, 'pdf'); }}
                                disabled={generating}
                                className="text-slate-400 hover:text-white p-1"
                              >
                                <FileText className="w-4 h-4" />
                              </Button>
                              <Button 
                                size="sm" 
                                variant="ghost" 
                                onClick={(e) => { e.stopPropagation(); generatePayslip(p.employee?.id, 'excel'); }}
                                disabled={generating}
                                className="text-slate-400 hover:text-white p-1"
                              >
                                <FileSpreadsheet className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detail Panel */}
        <div>
          {employeePayroll ? (
            <Card className="bg-slate-800/50 border-slate-700 sticky top-6">
              <CardHeader className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-t-lg">
                <CardTitle className="text-white">
                  Slip Gaji
                </CardTitle>
                <p className="text-blue-200 text-sm">
                  {employeePayroll.employee?.name} - {months.find(m => m.value === selectedMonth)?.label} {selectedYear}
                </p>
              </CardHeader>
              <CardContent className="p-4 space-y-4">
                {/* Employee Info */}
                <div className="bg-slate-700/50 p-3 rounded-lg text-sm">
                  <div className="grid grid-cols-2 gap-2">
                    <div><span className="text-slate-400">NIK:</span> <span className="text-white">{employeePayroll.employee?.nik}</span></div>
                    <div><span className="text-slate-400">Jabatan:</span> <span className="text-white">{employeePayroll.employee?.jabatan}</span></div>
                    <div><span className="text-slate-400">Cabang:</span> <span className="text-white">{employeePayroll.employee?.branch}</span></div>
                    <div><span className="text-slate-400">Tipe:</span> <span className="text-white">{employeePayroll.employee?.salary_type === 'monthly' ? 'Bulanan' : 'Harian'}</span></div>
                  </div>
                </div>

                {/* Attendance Summary */}
                <div>
                  <h4 className="text-slate-400 text-sm mb-2">Rekap Absensi</h4>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-green-900/30 p-2 rounded text-center">
                      <div className="text-lg font-bold text-green-400">{employeePayroll.attendance?.total_hadir}</div>
                      <div className="text-xs text-slate-400">Hadir</div>
                    </div>
                    <div className="bg-red-900/30 p-2 rounded text-center">
                      <div className="text-lg font-bold text-red-400">{employeePayroll.attendance?.total_alpha}</div>
                      <div className="text-xs text-slate-400">Alpha</div>
                    </div>
                    <div className="bg-yellow-900/30 p-2 rounded text-center">
                      <div className="text-lg font-bold text-yellow-400">{employeePayroll.attendance?.total_telat_menit}m</div>
                      <div className="text-xs text-slate-400">Telat</div>
                    </div>
                  </div>
                </div>

                {/* Earnings */}
                <div>
                  <h4 className="text-green-400 text-sm mb-2">Pendapatan</h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between text-slate-300">
                      <span>Gaji Dasar</span>
                      <span>{formatRupiah(employeePayroll.calculation?.gaji_dasar)}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Tunjangan</span>
                      <span>{formatRupiah(employeePayroll.calculation?.tunjangan?.total)}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Bonus Kehadiran</span>
                      <span>{formatRupiah(employeePayroll.calculation?.bonus?.kehadiran)}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Bonus Lembur</span>
                      <span>{formatRupiah(employeePayroll.calculation?.bonus?.lembur)}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Bonus Penjualan</span>
                      <span>{formatRupiah(employeePayroll.calculation?.bonus?.penjualan)}</span>
                    </div>
                    <div className="flex justify-between text-white font-medium border-t border-slate-600 pt-1">
                      <span>Total Gross</span>
                      <span>{formatRupiah(employeePayroll.calculation?.gross)}</span>
                    </div>
                  </div>
                </div>

                {/* Deductions */}
                <div>
                  <h4 className="text-red-400 text-sm mb-2">Potongan</h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between text-slate-300">
                      <span>Pot. Telat ({employeePayroll.attendance?.total_telat_menit}m)</span>
                      <span>-{formatRupiah(employeePayroll.calculation?.potongan?.telat)}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Pot. Alpha ({employeePayroll.attendance?.total_alpha} hari)</span>
                      <span>-{formatRupiah(employeePayroll.calculation?.potongan?.alpha)}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>BPJS Kesehatan</span>
                      <span>-{formatRupiah(employeePayroll.calculation?.potongan?.bpjs_kes)}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>BPJS TK</span>
                      <span>-{formatRupiah(employeePayroll.calculation?.potongan?.bpjs_tk)}</span>
                    </div>
                    <div className="flex justify-between text-white font-medium border-t border-slate-600 pt-1">
                      <span>Total Potongan</span>
                      <span>-{formatRupiah(employeePayroll.calculation?.potongan?.total)}</span>
                    </div>
                  </div>
                </div>

                {/* Take Home Pay */}
                <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-4 rounded-lg">
                  <div className="text-center">
                    <div className="text-green-200 text-sm">Take Home Pay</div>
                    <div className="text-3xl font-bold text-white">{formatRupiah(employeePayroll.calculation?.take_home_pay)}</div>
                  </div>
                </div>

                {/* Download Buttons */}
                <div className="flex gap-2">
                  <Button 
                    className="flex-1 bg-red-600 hover:bg-red-700" 
                    onClick={() => generatePayslip(employeePayroll.employee?.id, 'pdf')}
                    disabled={generating}
                    data-testid="download-pdf-btn"
                  >
                    <FileText className="w-4 h-4 mr-2" /> PDF
                  </Button>
                  <Button 
                    className="flex-1 bg-green-600 hover:bg-green-700" 
                    onClick={() => generatePayslip(employeePayroll.employee?.id, 'excel')}
                    disabled={generating}
                    data-testid="download-excel-btn"
                  >
                    <FileSpreadsheet className="w-4 h-4 mr-2" /> Excel
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-8 text-center">
                <Calculator className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">Pilih karyawan untuk melihat detail slip gaji</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
