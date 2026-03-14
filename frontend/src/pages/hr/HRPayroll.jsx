// OCB TITAN ERP - HR Payroll Dashboard
// Blueprint: SUPER DUPER DEWA
// Dark Theme Enterprise UI

import React, { useState, useEffect, useCallback } from 'react';
import { 
  DollarSign, Users, Calculator, FileText, Play, CheckCircle,
  RefreshCw, Download, Calendar, TrendingUp, Eye, Printer
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status Badge
const StatusBadge = ({ status }) => {
  const statusConfig = {
    draft: { label: 'Draft', class: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
    posted: { label: 'Posted', class: 'bg-green-500/20 text-green-400 border-green-500/30' },
    paid: { label: 'Paid', class: 'bg-blue-500/20 text-blue-400 border-blue-500/30' }
  };
  
  const config = statusConfig[status] || statusConfig.draft;
  
  return (
    <span className={`px-2 py-1 text-xs rounded-full border ${config.class}`}>
      {config.label}
    </span>
  );
};

// Payroll Slip Modal
const PayrollSlipModal = ({ isOpen, onClose, slip }) => {
  if (!isOpen || !slip) return null;
  
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
  };
  
  const allowances = slip.items?.allowances || [];
  const deductions = slip.items?.deductions || [];
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-700 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-orange-500" />
            Slip Gaji
          </h2>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-white"
          >
            ✕
          </button>
        </div>
        
        <div className="p-6">
          {/* Employee Info */}
          <div className="bg-slate-900 rounded-lg p-4 mb-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-400">NIK</p>
                <p className="text-white font-mono">{slip.employee_nik}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Periode</p>
                <p className="text-white">{slip.period}</p>
              </div>
            </div>
            <div className="mt-3">
              <p className="text-sm text-slate-400">Nama Karyawan</p>
              <p className="text-white font-medium text-lg">{slip.employee_name}</p>
            </div>
            <div className="mt-2">
              <p className="text-sm text-slate-400">Departemen</p>
              <p className="text-white">{slip.department_name}</p>
            </div>
          </div>
          
          {/* Earnings */}
          <div className="mb-4">
            <h3 className="text-white font-medium mb-2">Pendapatan</h3>
            <div className="bg-slate-900 rounded-lg divide-y divide-slate-700">
              <div className="flex justify-between p-3">
                <span className="text-slate-300">Gaji Pokok</span>
                <span className="text-green-400">{formatCurrency(slip.salary_base)}</span>
              </div>
              {allowances.map((item, idx) => (
                <div key={idx} className="flex justify-between p-3">
                  <span className="text-slate-300">{item.item_name}</span>
                  <span className="text-green-400">{formatCurrency(item.amount)}</span>
                </div>
              ))}
              <div className="flex justify-between p-3 bg-slate-800/50">
                <span className="text-white font-medium">Total Pendapatan</span>
                <span className="text-green-400 font-bold">{formatCurrency(slip.gross_salary)}</span>
              </div>
            </div>
          </div>
          
          {/* Deductions */}
          <div className="mb-4">
            <h3 className="text-white font-medium mb-2">Potongan</h3>
            <div className="bg-slate-900 rounded-lg divide-y divide-slate-700">
              {deductions.length > 0 ? (
                deductions.map((item, idx) => (
                  <div key={idx} className="flex justify-between p-3">
                    <span className="text-slate-300">{item.item_name}</span>
                    <span className="text-red-400">-{formatCurrency(item.amount)}</span>
                  </div>
                ))
              ) : (
                <div className="p-3 text-slate-500 text-center">Tidak ada potongan</div>
              )}
              {slip.tax_amount > 0 && (
                <div className="flex justify-between p-3">
                  <span className="text-slate-300">PPh 21</span>
                  <span className="text-red-400">-{formatCurrency(slip.tax_amount)}</span>
                </div>
              )}
              <div className="flex justify-between p-3 bg-slate-800/50">
                <span className="text-white font-medium">Total Potongan</span>
                <span className="text-red-400 font-bold">-{formatCurrency(slip.total_deductions + (slip.tax_amount || 0))}</span>
              </div>
            </div>
          </div>
          
          {/* Net Salary */}
          <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <span className="text-white font-medium text-lg">Gaji Bersih</span>
              <span className="text-green-400 font-bold text-2xl">{formatCurrency(slip.net_salary)}</span>
            </div>
          </div>
          
          {/* Journal Info */}
          {slip.journal_id && (
            <div className="mt-4 p-3 bg-slate-900 rounded-lg">
              <p className="text-sm text-slate-400">Journal Entry</p>
              <p className="text-white font-mono">{slip.journal_id}</p>
            </div>
          )}
          
          {/* Actions */}
          <div className="flex justify-end gap-3 mt-6">
            <Button
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              <Printer className="w-4 h-4 mr-2" />
              Print
            </Button>
            <Button
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              <Download className="w-4 h-4 mr-2" />
              Download PDF
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Run Payroll Modal
const RunPayrollModal = ({ isOpen, onClose, onRun }) => {
  const currentDate = new Date();
  const [month, setMonth] = useState(currentDate.getMonth() + 1);
  const [year, setYear] = useState(currentDate.getFullYear());
  const [running, setRunning] = useState(false);
  
  const handleRun = async () => {
    setRunning(true);
    await onRun(month, year);
    setRunning(false);
  };
  
  if (!isOpen) return null;
  
  const months = [
    { value: 1, label: 'Januari' },
    { value: 2, label: 'Februari' },
    { value: 3, label: 'Maret' },
    { value: 4, label: 'April' },
    { value: 5, label: 'Mei' },
    { value: 6, label: 'Juni' },
    { value: 7, label: 'Juli' },
    { value: 8, label: 'Agustus' },
    { value: 9, label: 'September' },
    { value: 10, label: 'Oktober' },
    { value: 11, label: 'November' },
    { value: 12, label: 'Desember' }
  ];
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md">
        <div className="p-6 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <Calculator className="w-5 h-5 text-orange-500" />
            Proses Payroll
          </h2>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Bulan</label>
            <select
              value={month}
              onChange={(e) => setMonth(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
              data-testid="payroll-month-select"
            >
              {months.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-1">Tahun</label>
            <Input
              type="number"
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value))}
              className="bg-slate-900 border-slate-700 text-white"
              data-testid="payroll-year-input"
            />
          </div>
          
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
            <p className="text-amber-400 text-sm">
              Payroll akan diproses untuk semua karyawan aktif. 
              Pastikan data attendance dan leave sudah lengkap sebelum proses.
            </p>
          </div>
          
          <div className="flex justify-end gap-3 pt-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={onClose}
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              disabled={running}
            >
              Batal
            </Button>
            <Button 
              onClick={handleRun}
              className="bg-green-600 hover:bg-green-700 text-white"
              disabled={running}
              data-testid="run-payroll-btn"
            >
              {running ? (
                <>Processing...</>
              ) : (
                <><Play className="w-4 h-4 mr-2" /> Proses Payroll</>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Component
const HRPayroll = () => {
  const [payrollData, setPayrollData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showRunModal, setShowRunModal] = useState(false);
  const [showSlipModal, setShowSlipModal] = useState(false);
  const [selectedSlip, setSelectedSlip] = useState(null);
  
  const currentDate = new Date();
  const [selectedPeriod, setSelectedPeriod] = useState(
    `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`
  );
  
  const token = localStorage.getItem('token');
  
  const fetchPayrollData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/hr/payroll/${selectedPeriod}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      
      setPayrollData(data.payrolls || []);
      setSummary(data.summary || null);
    } catch (error) {
      toast.error('Gagal memuat data payroll');
    }
    setLoading(false);
  }, [token, selectedPeriod]);
  
  useEffect(() => {
    fetchPayrollData();
  }, [fetchPayrollData]);
  
  const handleRunPayroll = async (month, year) => {
    try {
      const res = await fetch(`${API_URL}/api/hr/payroll/run`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          period_month: month,
          period_year: year
        })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(`Payroll berhasil diproses: ${data.batch_no}`);
        toast.info(`${data.summary.employee_count} karyawan, Total: Rp ${data.summary.total_net?.toLocaleString('id-ID')}`);
        setShowRunModal(false);
        setSelectedPeriod(`${year}-${String(month).padStart(2, '0')}`);
      } else {
        toast.error(data.detail || 'Gagal proses payroll');
      }
    } catch (error) {
      toast.error('Terjadi kesalahan');
    }
  };
  
  const handlePostPayroll = async (batchId) => {
    if (!window.confirm('Yakin ingin posting payroll ini? Journal akan dibuat otomatis.')) return;
    
    try {
      const res = await fetch(`${API_URL}/api/hr/payroll/post/${batchId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(`Payroll berhasil diposting: Journal ${data.journal_no}`);
        fetchPayrollData();
      } else {
        toast.error(data.detail || 'Gagal posting payroll');
      }
    } catch (error) {
      toast.error('Terjadi kesalahan');
    }
  };
  
  const handleViewSlip = async (payrollId) => {
    try {
      const res = await fetch(`${API_URL}/api/hr/payroll/slip/${payrollId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      
      setSelectedSlip(data);
      setShowSlipModal(true);
    } catch (error) {
      toast.error('Gagal memuat slip gaji');
    }
  };
  
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
  };
  
  // Get unique batch_id for posting
  const draftBatchId = payrollData.find(p => p.status === 'draft')?.batch_id;
  
  return (
    <div className="min-h-screen bg-slate-900 p-6" data-testid="hr-payroll-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <DollarSign className="w-8 h-8 text-orange-500" />
          Dashboard Payroll
        </h1>
        <p className="text-slate-400 mt-1">Payroll Engine - Auto Journal Integration</p>
      </div>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Users className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Karyawan</p>
              <p className="text-2xl font-bold text-white">{summary?.employee_count || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Total Gross</p>
              <p className="text-xl font-bold text-green-400">
                {formatCurrency(summary?.total_gross)}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <Calculator className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Total Potongan</p>
              <p className="text-xl font-bold text-red-400">
                {formatCurrency((summary?.total_deductions || 0) + (summary?.total_tax || 0))}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <DollarSign className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Total Net</p>
              <p className="text-xl font-bold text-purple-400">
                {formatCurrency(summary?.total_net)}
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Toolbar */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button 
              onClick={() => setShowRunModal(true)}
              className="bg-green-600 hover:bg-green-700 text-white"
              data-testid="run-payroll-modal-btn"
            >
              <Play className="w-4 h-4 mr-2" />
              Proses Payroll
            </Button>
            
            {draftBatchId && (
              <Button 
                onClick={() => handlePostPayroll(draftBatchId)}
                className="bg-blue-600 hover:bg-blue-700 text-white"
                data-testid="post-payroll-btn"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Post Payroll
              </Button>
            )}
            
            <Button
              onClick={fetchPayrollData}
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-slate-400" />
              <Input
                type="month"
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="bg-slate-900 border-slate-700 text-white w-44"
                data-testid="period-filter"
              />
            </div>
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
        <div className="p-4 border-b border-slate-700">
          <h3 className="text-white font-medium">Payroll Periode: {selectedPeriod}</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="payroll-table">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">NIK</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Nama</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Departemen</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-slate-300">Gaji Pokok</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-slate-300">Tunjangan</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-slate-300">Potongan</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-slate-300">PPh 21</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-slate-300">Net Salary</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Status</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {loading ? (
                <tr>
                  <td colSpan="10" className="px-4 py-8 text-center text-slate-400">
                    Memuat data...
                  </td>
                </tr>
              ) : payrollData.length === 0 ? (
                <tr>
                  <td colSpan="10" className="px-4 py-8 text-center text-slate-400">
                    Tidak ada data payroll untuk periode ini
                  </td>
                </tr>
              ) : (
                payrollData.map((payroll) => (
                  <tr 
                    key={payroll.id} 
                    className="hover:bg-slate-700/30 transition-colors"
                    data-testid={`payroll-row-${payroll.id}`}
                  >
                    <td className="px-4 py-3 text-sm text-white font-mono">
                      {payroll.employee_nik}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-white font-medium">
                        {payroll.employee_name}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {payroll.department_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-white">
                      {formatCurrency(payroll.salary_base)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-green-400">
                      +{formatCurrency(payroll.total_allowances)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-red-400">
                      -{formatCurrency(payroll.total_deductions)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-amber-400">
                      -{formatCurrency(payroll.tax_amount)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-purple-400 font-bold">
                      {formatCurrency(payroll.net_salary)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusBadge status={payroll.status} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => handleViewSlip(payroll.id)}
                          className="p-1.5 text-blue-400 hover:bg-blue-500/20 rounded transition-colors"
                          title="Lihat Slip"
                          data-testid={`view-slip-btn-${payroll.id}`}
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
        
        {/* Footer Summary */}
        {summary && payrollData.length > 0 && (
          <div className="px-4 py-3 border-t border-slate-700 bg-slate-900/50">
            <div className="flex justify-end gap-8">
              <div className="text-right">
                <p className="text-sm text-slate-400">Total Gross</p>
                <p className="text-green-400 font-bold">{formatCurrency(summary.total_gross)}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-400">Total Net</p>
                <p className="text-purple-400 font-bold text-lg">{formatCurrency(summary.total_net)}</p>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Modals */}
      <RunPayrollModal
        isOpen={showRunModal}
        onClose={() => setShowRunModal(false)}
        onRun={handleRunPayroll}
      />
      
      <PayrollSlipModal
        isOpen={showSlipModal}
        onClose={() => { setShowSlipModal(false); setSelectedSlip(null); }}
        slip={selectedSlip}
      />
    </div>
  );
};

export default HRPayroll;
