import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { 
  FileText, RefreshCw, Download, Calendar, TrendingUp, 
  TrendingDown, DollarSign, BarChart3, PieChart, Wallet,
  ArrowRight, CheckCircle, XCircle
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function FinancialReports() {
  const [activeReport, setActiveReport] = useState('trial-balance');
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  
  // Filters
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]);
  const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  
  const token = localStorage.getItem('token');

  const fetchReport = useCallback(async (reportType) => {
    setLoading(true);
    try {
      let url = `${API}/api/accounting/${reportType}`;
      const params = new URLSearchParams();
      
      if (reportType === 'trial-balance' || reportType === 'balance-sheet') {
        params.append('as_of_date', asOfDate);
      } else if (reportType === 'income-statement') {
        params.append('start_date', startDate);
        params.append('end_date', endDate);
      }
      
      if (params.toString()) {
        url += `?${params}`;
      }
      
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setReportData(data);
      }
    } catch (err) {
      console.error('Error fetching report:', err);
    } finally {
      setLoading(false);
    }
  }, [token, asOfDate, startDate, endDate]);

  useEffect(() => {
    fetchReport(activeReport);
  }, [activeReport, fetchReport]);

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('id-ID', { 
      style: 'currency', 
      currency: 'IDR',
      minimumFractionDigits: 0 
    }).format(val || 0);
  };

  const exportToCSV = () => {
    if (!reportData) return;
    
    let csv = '';
    let filename = '';
    
    if (activeReport === 'trial-balance') {
      csv = 'Kode,Nama Akun,Tipe,Debit,Credit\n';
      reportData.accounts?.forEach(acc => {
        csv += `${acc.code},"${acc.name}",${acc.type},${acc.debit},${acc.credit}\n`;
      });
      filename = `trial_balance_${asOfDate}.csv`;
    } else if (activeReport === 'balance-sheet') {
      csv = 'Kategori,Kode,Nama Akun,Saldo\n';
      ['assets', 'liabilities', 'equity'].forEach(cat => {
        reportData[cat]?.items?.forEach(acc => {
          csv += `${cat},${acc.code},"${acc.name}",${acc.balance || acc.debit || acc.credit}\n`;
        });
      });
      filename = `neraca_${asOfDate}.csv`;
    } else if (activeReport === 'income-statement') {
      csv = 'Kategori,Kode,Nama Akun,Jumlah\n';
      reportData.revenues?.items?.forEach(acc => {
        csv += `Pendapatan,${acc.code},"${acc.name}",${acc.amount}\n`;
      });
      reportData.expenses?.items?.forEach(acc => {
        csv += `Beban,${acc.code},"${acc.name}",${acc.amount}\n`;
      });
      filename = `laba_rugi_${startDate}_${endDate}.csv`;
    }
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  };

  const REPORT_TYPES = [
    { key: 'trial-balance', label: 'Trial Balance', icon: BarChart3, color: 'blue' },
    { key: 'balance-sheet', label: 'Neraca', icon: PieChart, color: 'green' },
    { key: 'income-statement', label: 'Laba Rugi', icon: TrendingUp, color: 'purple' }
  ];

  return (
    <div className="p-6 space-y-6" data-testid="financial-reports-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Laporan Keuangan</h1>
          <p className="text-gray-500 text-sm mt-1">Trial Balance, Neraca, Laba Rugi</p>
        </div>
        <Button onClick={exportToCSV} variant="outline" data-testid="btn-export">
          <Download className="w-4 h-4 mr-2" />
          Export CSV
        </Button>
      </div>

      {/* Report Type Selector */}
      <div className="grid grid-cols-3 gap-4">
        {REPORT_TYPES.map(report => {
          const Icon = report.icon;
          const isActive = activeReport === report.key;
          
          return (
            <Card 
              key={report.key}
              className={`cursor-pointer transition-all ${
                isActive 
                  ? `border-2 border-${report.color}-500 bg-${report.color}-50` 
                  : 'hover:shadow-md'
              }`}
              onClick={() => setActiveReport(report.key)}
              data-testid={`report-${report.key}`}
            >
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-lg ${isActive ? `bg-${report.color}-100` : 'bg-gray-100'}`}>
                    <Icon className={`w-6 h-6 ${isActive ? `text-${report.color}-600` : 'text-gray-600'}`} />
                  </div>
                  <div>
                    <p className={`font-medium ${isActive ? `text-${report.color}-700` : 'text-gray-700'}`}>
                      {report.label}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Date Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-end gap-4">
            {(activeReport === 'trial-balance' || activeReport === 'balance-sheet') ? (
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">
                  Per Tanggal
                </label>
                <Input
                  type="date"
                  value={asOfDate}
                  onChange={(e) => setAsOfDate(e.target.value)}
                  className="w-48"
                  data-testid="as-of-date"
                />
              </div>
            ) : (
              <>
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1 block">
                    Dari Tanggal
                  </label>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-48"
                    data-testid="start-date"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1 block">
                    Sampai Tanggal
                  </label>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-48"
                    data-testid="end-date"
                  />
                </div>
              </>
            )}
            <Button onClick={() => fetchReport(activeReport)} data-testid="btn-generate">
              <RefreshCw className="w-4 h-4 mr-2" />
              Generate
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Report Content */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
          <span className="ml-2 text-gray-500">Memuat laporan...</span>
        </div>
      ) : reportData ? (
        <>
          {/* Trial Balance */}
          {activeReport === 'trial-balance' && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    Trial Balance
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge className={reportData.is_balanced ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                      {reportData.is_balanced ? (
                        <><CheckCircle className="w-3 h-3 mr-1" /> Balanced</>
                      ) : (
                        <><XCircle className="w-3 h-3 mr-1" /> Not Balanced</>
                      )}
                    </Badge>
                  </div>
                </div>
                <p className="text-sm text-gray-500">Per {asOfDate}</p>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-gray-600">Kode</th>
                        <th className="px-4 py-3 text-left font-medium text-gray-600">Nama Akun</th>
                        <th className="px-4 py-3 text-center font-medium text-gray-600">Kategori</th>
                        <th className="px-4 py-3 text-right font-medium text-gray-600">Debit</th>
                        <th className="px-4 py-3 text-right font-medium text-gray-600">Credit</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {reportData.items?.map((acc, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-mono">{acc.account_code}</td>
                          <td className="px-4 py-3">{acc.account_name}</td>
                          <td className="px-4 py-3 text-center">
                            <Badge variant="outline">{acc.category}</Badge>
                          </td>
                          <td className="px-4 py-3 text-right font-mono">
                            {acc.debit_balance > 0 ? formatCurrency(acc.debit_balance) : '-'}
                          </td>
                          <td className="px-4 py-3 text-right font-mono">
                            {acc.credit_balance > 0 ? formatCurrency(acc.credit_balance) : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-gray-100 font-bold">
                      <tr>
                        <td colSpan="3" className="px-4 py-3 text-right">TOTAL</td>
                        <td className="px-4 py-3 text-right font-mono text-blue-600">
                          {formatCurrency(reportData.total_debit)}
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-blue-600">
                          {formatCurrency(reportData.total_credit)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Balance Sheet / Neraca */}
          {activeReport === 'balance-sheet' && (
            <div className="grid grid-cols-2 gap-6">
              {/* Assets */}
              <Card>
                <CardHeader className="bg-blue-50">
                  <CardTitle className="text-lg flex items-center gap-2 text-blue-700">
                    <Wallet className="w-5 h-5" />
                    AKTIVA (Assets)
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <table className="w-full text-sm">
                    <tbody className="divide-y">
                      {reportData.assets?.items?.map((acc, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-2 font-mono text-xs">{acc.code}</td>
                          <td className="px-4 py-2">{acc.name}</td>
                          <td className="px-4 py-2 text-right font-mono">
                            {formatCurrency(acc.balance || acc.debit)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-blue-100">
                      <tr className="font-bold">
                        <td colSpan="2" className="px-4 py-3">Total Aktiva</td>
                        <td className="px-4 py-3 text-right font-mono text-blue-700">
                          {formatCurrency(reportData.assets?.total)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </CardContent>
              </Card>

              {/* Liabilities & Equity */}
              <div className="space-y-6">
                {/* Liabilities */}
                <Card>
                  <CardHeader className="bg-red-50">
                    <CardTitle className="text-lg flex items-center gap-2 text-red-700">
                      <TrendingDown className="w-5 h-5" />
                      KEWAJIBAN (Liabilities)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <table className="w-full text-sm">
                      <tbody className="divide-y">
                        {reportData.liabilities?.items?.map((acc, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-4 py-2 font-mono text-xs">{acc.code}</td>
                            <td className="px-4 py-2">{acc.name}</td>
                            <td className="px-4 py-2 text-right font-mono">
                              {formatCurrency(acc.balance || acc.credit)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot className="bg-red-100">
                        <tr className="font-bold">
                          <td colSpan="2" className="px-4 py-3">Total Kewajiban</td>
                          <td className="px-4 py-3 text-right font-mono text-red-700">
                            {formatCurrency(reportData.liabilities?.total)}
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </CardContent>
                </Card>

                {/* Equity */}
                <Card>
                  <CardHeader className="bg-green-50">
                    <CardTitle className="text-lg flex items-center gap-2 text-green-700">
                      <DollarSign className="w-5 h-5" />
                      EKUITAS (Equity)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <table className="w-full text-sm">
                      <tbody className="divide-y">
                        {reportData.equity?.items?.map((acc, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-4 py-2 font-mono text-xs">{acc.code}</td>
                            <td className="px-4 py-2">{acc.name}</td>
                            <td className="px-4 py-2 text-right font-mono">
                              {formatCurrency(acc.balance || acc.credit)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot className="bg-green-100">
                        <tr className="font-bold">
                          <td colSpan="2" className="px-4 py-3">Total Ekuitas</td>
                          <td className="px-4 py-3 text-right font-mono text-green-700">
                            {formatCurrency(reportData.equity?.total)}
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </CardContent>
                </Card>
              </div>

              {/* Balance Check */}
              <Card className="col-span-2">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="text-center">
                        <p className="text-sm text-gray-500">Total Aktiva</p>
                        <p className="text-xl font-mono font-bold text-blue-600">
                          {formatCurrency(reportData.assets?.total)}
                        </p>
                      </div>
                      <ArrowRight className="w-6 h-6 text-gray-400" />
                      <div className="text-center">
                        <p className="text-sm text-gray-500">Kewajiban + Ekuitas</p>
                        <p className="text-xl font-mono font-bold text-green-600">
                          {formatCurrency((reportData.liabilities?.total || 0) + (reportData.equity?.total || 0))}
                        </p>
                      </div>
                    </div>
                    <Badge className={reportData.is_balanced ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                      {reportData.is_balanced ? 'BALANCED' : 'NOT BALANCED'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Income Statement / Laba Rugi */}
          {activeReport === 'income-statement' && (
            <div className="space-y-6">
              <Card>
                <CardHeader className="bg-green-50">
                  <CardTitle className="text-lg flex items-center gap-2 text-green-700">
                    <TrendingUp className="w-5 h-5" />
                    PENDAPATAN (Revenue)
                  </CardTitle>
                  <p className="text-sm text-gray-500">
                    Periode: {startDate} s/d {endDate}
                  </p>
                </CardHeader>
                <CardContent className="p-0">
                  <table className="w-full text-sm">
                    <tbody className="divide-y">
                      {reportData.revenues?.items?.map((acc, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-2 font-mono text-xs">{acc.code}</td>
                          <td className="px-4 py-2">{acc.name}</td>
                          <td className="px-4 py-2 text-right font-mono text-green-600">
                            {formatCurrency(acc.amount)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-green-100">
                      <tr className="font-bold">
                        <td colSpan="2" className="px-4 py-3">Total Pendapatan</td>
                        <td className="px-4 py-3 text-right font-mono text-green-700">
                          {formatCurrency(reportData.revenues?.total)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="bg-red-50">
                  <CardTitle className="text-lg flex items-center gap-2 text-red-700">
                    <TrendingDown className="w-5 h-5" />
                    BEBAN (Expenses)
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <table className="w-full text-sm">
                    <tbody className="divide-y">
                      {reportData.expenses?.items?.map((acc, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-2 font-mono text-xs">{acc.code}</td>
                          <td className="px-4 py-2">{acc.name}</td>
                          <td className="px-4 py-2 text-right font-mono text-red-600">
                            {formatCurrency(acc.amount)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-red-100">
                      <tr className="font-bold">
                        <td colSpan="2" className="px-4 py-3">Total Beban</td>
                        <td className="px-4 py-3 text-right font-mono text-red-700">
                          {formatCurrency(reportData.expenses?.total)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </CardContent>
              </Card>

              {/* Net Income */}
              <Card className={reportData.is_profit ? 'border-2 border-green-500' : 'border-2 border-red-500'}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-lg font-medium text-gray-700">
                        {reportData.is_profit ? 'LABA BERSIH' : 'RUGI BERSIH'}
                      </p>
                      <p className="text-sm text-gray-500">
                        Pendapatan - Beban
                      </p>
                    </div>
                    <p className={`text-3xl font-mono font-bold ${
                      reportData.is_profit ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(Math.abs(reportData.net_income))}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Pilih laporan dan klik Generate</p>
        </div>
      )}
    </div>
  );
}
