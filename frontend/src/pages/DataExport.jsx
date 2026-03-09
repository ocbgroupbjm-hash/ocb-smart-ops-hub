import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Download, FileSpreadsheet, FileJson, FileText, 
  Database, Users, ShoppingCart, Package, Wallet,
  Building2, ClipboardList, AlertCircle, CheckCircle,
  Loader2, Calendar
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const DataExport = () => {
  const [loading, setLoading] = useState({});
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [periodId, setPeriodId] = useState('');
  const [exportFormat, setExportFormat] = useState('json');

  const downloadFile = async (endpoint, filename, format = 'json') => {
    setLoading(prev => ({ ...prev, [endpoint]: true }));
    try {
      const response = await fetch(`${API}/api/export/${endpoint}?format=${format}`, {
        method: 'GET',
      });
      
      if (!response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      
      toast.success(`Export ${filename} berhasil!`);
    } catch (err) {
      console.error('Export error:', err);
      toast.error('Gagal export data');
    } finally {
      setLoading(prev => ({ ...prev, [endpoint]: false }));
    }
  };

  const downloadWithParams = async (endpoint, filename, params = {}) => {
    setLoading(prev => ({ ...prev, [endpoint]: true }));
    try {
      const queryString = new URLSearchParams({ ...params, format: exportFormat }).toString();
      const response = await fetch(`${API}/api/export/${endpoint}?${queryString}`, {
        method: 'GET',
      });
      
      if (!response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      
      toast.success(`Export ${filename} berhasil!`);
    } catch (err) {
      console.error('Export error:', err);
      toast.error('Gagal export data');
    } finally {
      setLoading(prev => ({ ...prev, [endpoint]: false }));
    }
  };

  const ExportButton = ({ endpoint, filename, icon: Icon, label, format }) => (
    <Button
      variant="outline"
      className="w-full justify-start gap-2 bg-red-950/30 border-red-700/30 hover:bg-red-900/40 text-amber-100"
      onClick={() => downloadFile(endpoint, filename, format || exportFormat)}
      disabled={loading[endpoint]}
      data-testid={`export-${endpoint}`}
    >
      {loading[endpoint] ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Icon className="h-4 w-4" />
      )}
      {label}
      <Badge variant="outline" className="ml-auto text-xs">{format || exportFormat}</Badge>
    </Button>
  );

  const months = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0608] to-[#1a0a0e] p-4" data-testid="data-export-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
          <Download className="h-6 w-6 text-red-400" />
          Global Data Export System
        </h1>
        <p className="text-sm text-gray-400">Export semua data dalam format Excel, CSV, PDF, JSON</p>
      </div>

      {/* Format Selection */}
      <Card className="bg-[#120a0c]/80 border-red-900/30 mb-4">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Label className="text-amber-100">Format Export:</Label>
              <Select value={exportFormat} onValueChange={setExportFormat}>
                <SelectTrigger className="w-32 bg-red-950/50 border-red-700/30">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="json">
                    <div className="flex items-center gap-2">
                      <FileJson className="h-4 w-4" />
                      JSON
                    </div>
                  </SelectItem>
                  <SelectItem value="csv">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      CSV
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <Label className="text-amber-100">Periode:</Label>
              <Select value={selectedMonth.toString()} onValueChange={(v) => setSelectedMonth(parseInt(v))}>
                <SelectTrigger className="w-32 bg-red-950/50 border-red-700/30">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {months.map((m, i) => (
                    <SelectItem key={i} value={(i + 1).toString()}>{m}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v))}>
                <SelectTrigger className="w-24 bg-red-950/50 border-red-700/30">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[2024, 2025, 2026].map((y) => (
                    <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <Label className="text-amber-100">Range:</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-36 bg-red-950/50 border-red-700/30"
              />
              <span className="text-gray-400">-</span>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-36 bg-red-950/50 border-red-700/30"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="master" className="space-y-4">
        <TabsList className="bg-red-950/50 p-1">
          <TabsTrigger value="master" className="data-[state=active]:bg-red-900/50">
            <Database className="h-4 w-4 mr-1" />
            Master Data
          </TabsTrigger>
          <TabsTrigger value="hr" className="data-[state=active]:bg-red-900/50">
            <Users className="h-4 w-4 mr-1" />
            HR & Payroll
          </TabsTrigger>
          <TabsTrigger value="sales" className="data-[state=active]:bg-red-900/50">
            <ShoppingCart className="h-4 w-4 mr-1" />
            Penjualan
          </TabsTrigger>
          <TabsTrigger value="inventory" className="data-[state=active]:bg-red-900/50">
            <Package className="h-4 w-4 mr-1" />
            Persediaan
          </TabsTrigger>
          <TabsTrigger value="accounting" className="data-[state=active]:bg-red-900/50">
            <Wallet className="h-4 w-4 mr-1" />
            Akuntansi
          </TabsTrigger>
          <TabsTrigger value="audit" className="data-[state=active]:bg-red-900/50">
            <ClipboardList className="h-4 w-4 mr-1" />
            Audit & CRM
          </TabsTrigger>
        </TabsList>

        {/* Master Data */}
        <TabsContent value="master">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Produk & Kategori
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <ExportButton endpoint="master/products" filename="products" icon={Package} label="Export Produk" />
                <ExportButton endpoint="master/categories" filename="categories" icon={Database} label="Export Kategori" />
                <ExportButton endpoint="master/brands" filename="brands" icon={Database} label="Export Merk" />
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Supplier & Pelanggan
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <ExportButton endpoint="master/suppliers" filename="suppliers" icon={Users} label="Export Supplier" />
                <ExportButton endpoint="master/customers" filename="customers" icon={Users} label="Export Pelanggan" />
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  Cabang & Gudang
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <ExportButton endpoint="master/branches" filename="branches" icon={Building2} label="Export Cabang" />
                <ExportButton endpoint="master/warehouses" filename="warehouses" icon={Building2} label="Export Gudang" />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* HR & Payroll */}
        <TabsContent value="hr">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Data Karyawan
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <ExportButton endpoint="employees/all" filename="employees" icon={Users} label="Export Karyawan" />
                <ExportButton endpoint="employees/jabatan" filename="jabatan" icon={Database} label="Export Jabatan" />
                <ExportButton endpoint="employees/kpi" filename="kpi" icon={ClipboardList} label="Export KPI" />
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Absensi
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2 bg-red-950/30 border-red-700/30 hover:bg-red-900/40 text-amber-100"
                  onClick={() => downloadWithParams('employees/attendance', `attendance_${selectedYear}${selectedMonth}`, { month: selectedMonth, year: selectedYear })}
                  disabled={loading['employees/attendance']}
                >
                  {loading['employees/attendance'] ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Calendar className="h-4 w-4" />
                  )}
                  Export Absensi {months[selectedMonth - 1]}
                  <Badge variant="outline" className="ml-auto text-xs">{exportFormat}</Badge>
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Wallet className="h-4 w-4" />
                  Payroll
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex gap-2">
                  <Input
                    placeholder="Period ID"
                    value={periodId}
                    onChange={(e) => setPeriodId(e.target.value)}
                    className="bg-red-950/50 border-red-700/30"
                  />
                  <Button
                    variant="outline"
                    className="bg-red-950/30 border-red-700/30 hover:bg-red-900/40"
                    onClick={() => downloadWithParams('payroll/details', `payroll_${periodId}`, { period_id: periodId })}
                    disabled={loading['payroll/details'] || !periodId}
                  >
                    {loading['payroll/details'] ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Sales */}
        <TabsContent value="sales">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <ShoppingCart className="h-4 w-4" />
                  Transaksi
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2 bg-red-950/30 border-red-700/30 hover:bg-red-900/40 text-amber-100"
                  onClick={() => downloadWithParams('sales/transactions', `transactions_${startDate}_${endDate}`, { start_date: startDate, end_date: endDate })}
                  disabled={loading['sales/transactions']}
                >
                  {loading['sales/transactions'] ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <ShoppingCart className="h-4 w-4" />
                  )}
                  Export Transaksi ({startDate} - {endDate})
                  <Badge variant="outline" className="ml-auto text-xs">{exportFormat}</Badge>
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Wallet className="h-4 w-4" />
                  Setoran Harian
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2 bg-red-950/30 border-red-700/30 hover:bg-red-900/40 text-amber-100"
                  onClick={() => downloadWithParams('sales/setoran', `setoran_${selectedYear}${selectedMonth}`, { month: selectedMonth, year: selectedYear })}
                  disabled={loading['sales/setoran']}
                >
                  {loading['sales/setoran'] ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Wallet className="h-4 w-4" />
                  )}
                  Export Setoran {months[selectedMonth - 1]}
                  <Badge variant="outline" className="ml-auto text-xs">{exportFormat}</Badge>
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  Selisih Kas
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2 bg-red-950/30 border-red-700/30 hover:bg-red-900/40 text-amber-100"
                  onClick={() => downloadWithParams('sales/selisih', `selisih_${selectedYear}${selectedMonth}`, { month: selectedMonth, year: selectedYear })}
                  disabled={loading['sales/selisih']}
                >
                  {loading['sales/selisih'] ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  Export Selisih Kas {months[selectedMonth - 1]}
                  <Badge variant="outline" className="ml-auto text-xs">{exportFormat}</Badge>
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Inventory */}
        <TabsContent value="inventory">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Stok
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <ExportButton endpoint="inventory/stock" filename="stock" icon={Package} label="Export Stok Saat Ini" />
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <ClipboardList className="h-4 w-4" />
                  Mutasi Stok
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2 bg-red-950/30 border-red-700/30 hover:bg-red-900/40 text-amber-100"
                  onClick={() => downloadWithParams('inventory/mutations', `mutations_${startDate}_${endDate}`, { start_date: startDate, end_date: endDate })}
                  disabled={loading['inventory/mutations']}
                >
                  {loading['inventory/mutations'] ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <ClipboardList className="h-4 w-4" />
                  )}
                  Export Mutasi ({startDate} - {endDate})
                  <Badge variant="outline" className="ml-auto text-xs">{exportFormat}</Badge>
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Accounting */}
        <TabsContent value="accounting">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <FileSpreadsheet className="h-4 w-4" />
                  Jurnal
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2 bg-red-950/30 border-red-700/30 hover:bg-red-900/40 text-amber-100"
                  onClick={() => downloadWithParams('accounting/journals', `journals_${selectedYear}${selectedMonth}`, { month: selectedMonth, year: selectedYear })}
                  disabled={loading['accounting/journals']}
                >
                  {loading['accounting/journals'] ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <FileSpreadsheet className="h-4 w-4" />
                  )}
                  Export Jurnal {months[selectedMonth - 1]}
                  <Badge variant="outline" className="ml-auto text-xs">{exportFormat}</Badge>
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Wallet className="h-4 w-4" />
                  Kas Masuk/Keluar
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2 bg-red-950/30 border-red-700/30 hover:bg-red-900/40 text-amber-100"
                  onClick={() => downloadWithParams('accounting/kas-masuk', `kas_masuk_${selectedYear}${selectedMonth}`, { month: selectedMonth, year: selectedYear })}
                  disabled={loading['accounting/kas-masuk']}
                >
                  {loading['accounting/kas-masuk'] ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4 text-green-400" />
                  )}
                  Export Kas Masuk
                  <Badge variant="outline" className="ml-auto text-xs">{exportFormat}</Badge>
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2 bg-red-950/30 border-red-700/30 hover:bg-red-900/40 text-amber-100"
                  onClick={() => downloadWithParams('accounting/kas-keluar', `kas_keluar_${selectedYear}${selectedMonth}`, { month: selectedMonth, year: selectedYear })}
                  disabled={loading['accounting/kas-keluar']}
                >
                  {loading['accounting/kas-keluar'] ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4 text-red-400" />
                  )}
                  Export Kas Keluar
                  <Badge variant="outline" className="ml-auto text-xs">{exportFormat}</Badge>
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Audit & CRM */}
        <TabsContent value="audit">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <ClipboardList className="h-4 w-4" />
                  Audit
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <ExportButton endpoint="audit/kas" filename="audit_kas" icon={Wallet} label="Export Audit Kas" />
                <ExportButton endpoint="audit/stock" filename="audit_stock" icon={Package} label="Export Audit Stok" />
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  CRM
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <ExportButton endpoint="crm/customers" filename="crm_customers" icon={Users} label="Export CRM Customers" />
                <ExportButton endpoint="crm/complaints" filename="complaints" icon={AlertCircle} label="Export Komplain" />
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Database className="h-4 w-4" />
                  Bulk Export
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2 bg-gradient-to-r from-red-900/50 to-amber-900/30 border-amber-700/30 hover:from-red-800/50 hover:to-amber-800/30 text-amber-100"
                  onClick={() => downloadFile('bulk/all', 'ocb_full_export', 'json')}
                  disabled={loading['bulk/all']}
                >
                  {loading['bulk/all'] ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Database className="h-4 w-4" />
                  )}
                  Export SEMUA Data
                  <Badge className="ml-auto bg-amber-600">JSON</Badge>
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Status */}
      <Card className="bg-[#120a0c]/80 border-green-900/30 mt-4">
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-400" />
            <span className="text-green-400 font-medium">Sistem Export Aktif</span>
            <span className="text-gray-500 text-sm ml-2">
              Semua data dapat di-export dalam format JSON dan CSV
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DataExport;
