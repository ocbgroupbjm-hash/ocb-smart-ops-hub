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
  Download, FileSpreadsheet, FileJson, FileText, File,
  Database, Users, ShoppingCart, Package, Wallet, Building2,
  ClipboardList, AlertCircle, CheckCircle, Loader2, Calendar,
  Trophy, TrendingUp, Bell
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const AdvancedExport = () => {
  const [loading, setLoading] = useState({});
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  const downloadFile = async (endpoint, filename, format = 'xlsx') => {
    const key = `${endpoint}_${format}`;
    setLoading(prev => ({ ...prev, [key]: true }));
    try {
      const response = await fetch(`${API}/api/export-v2/${endpoint}?format=${format}&month=${selectedMonth}&year=${selectedYear}&start_date=${startDate}&end_date=${endDate}`);
      
      if (!response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}_${selectedYear}${selectedMonth.toString().padStart(2, '0')}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      
      toast.success(`Export ${filename} (${format.toUpperCase()}) berhasil!`);
    } catch (err) {
      console.error('Export error:', err);
      toast.error('Gagal export data');
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const ExportButton = ({ endpoint, filename, icon: Icon, label }) => {
    const formats = ['xlsx', 'pdf', 'csv', 'json'];
    
    return (
      <div className="p-3 bg-red-950/30 rounded-lg border border-red-900/30">
        <div className="flex items-center gap-2 mb-2">
          <Icon className="h-4 w-4 text-amber-400" />
          <span className="text-sm font-medium text-amber-100">{label}</span>
        </div>
        <div className="grid grid-cols-4 gap-1">
          {formats.map((format) => {
            const key = `${endpoint}_${format}`;
            const FormatIcon = format === 'xlsx' ? FileSpreadsheet : 
                             format === 'pdf' ? File :
                             format === 'csv' ? FileText : FileJson;
            return (
              <Button
                key={format}
                size="sm"
                variant="outline"
                className="h-8 text-xs bg-red-950/50 border-red-700/30 hover:bg-red-900/50"
                onClick={() => downloadFile(endpoint, filename, format)}
                disabled={loading[key]}
                data-testid={`export-${endpoint}-${format}`}
              >
                {loading[key] ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <>
                    <FormatIcon className="h-3 w-3 mr-1" />
                    {format.toUpperCase()}
                  </>
                )}
              </Button>
            );
          })}
        </div>
      </div>
    );
  };

  const months = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0608] to-[#1a0a0e] p-4" data-testid="advanced-export-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
          <Download className="h-6 w-6 text-green-400" />
          Advanced Export System
        </h1>
        <p className="text-sm text-gray-400">Export ke Excel, PDF, CSV, JSON untuk semua modul</p>
      </div>

      {/* Period Selection */}
      <Card className="bg-[#120a0c]/80 border-red-900/30 mb-4">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
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

            <div className="flex gap-1 ml-auto">
              <Badge className="bg-green-600"><FileSpreadsheet className="h-3 w-3 mr-1" />Excel</Badge>
              <Badge className="bg-red-600"><File className="h-3 w-3 mr-1" />PDF</Badge>
              <Badge className="bg-blue-600"><FileText className="h-3 w-3 mr-1" />CSV</Badge>
              <Badge className="bg-yellow-600"><FileJson className="h-3 w-3 mr-1" />JSON</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="master" className="space-y-4">
        <TabsList className="bg-red-950/50 p-1 flex-wrap">
          <TabsTrigger value="master" className="data-[state=active]:bg-red-900/50">
            <Database className="h-4 w-4 mr-1" />
            Master
          </TabsTrigger>
          <TabsTrigger value="hr" className="data-[state=active]:bg-red-900/50">
            <Users className="h-4 w-4 mr-1" />
            HR
          </TabsTrigger>
          <TabsTrigger value="kpi" className="data-[state=active]:bg-red-900/50">
            <Trophy className="h-4 w-4 mr-1" />
            KPI
          </TabsTrigger>
          <TabsTrigger value="sales" className="data-[state=active]:bg-red-900/50">
            <ShoppingCart className="h-4 w-4 mr-1" />
            Sales
          </TabsTrigger>
          <TabsTrigger value="inventory" className="data-[state=active]:bg-red-900/50">
            <Package className="h-4 w-4 mr-1" />
            Inventory
          </TabsTrigger>
          <TabsTrigger value="accounting" className="data-[state=active]:bg-red-900/50">
            <Wallet className="h-4 w-4 mr-1" />
            Accounting
          </TabsTrigger>
          <TabsTrigger value="audit" className="data-[state=active]:bg-red-900/50">
            <ClipboardList className="h-4 w-4 mr-1" />
            Audit/CRM
          </TabsTrigger>
          <TabsTrigger value="alerts" className="data-[state=active]:bg-red-900/50">
            <Bell className="h-4 w-4 mr-1" />
            Alerts
          </TabsTrigger>
        </TabsList>

        {/* Master Data */}
        <TabsContent value="master">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <ExportButton endpoint="master/products" filename="products" icon={Package} label="Produk / Items" />
            <ExportButton endpoint="master/categories" filename="categories" icon={Database} label="Kategori" />
            <ExportButton endpoint="master/brands" filename="brands" icon={Database} label="Merk / Brand" />
            <ExportButton endpoint="master/suppliers" filename="suppliers" icon={Users} label="Supplier" />
            <ExportButton endpoint="master/customers" filename="customers" icon={Users} label="Pelanggan" />
            <ExportButton endpoint="master/branches" filename="branches" icon={Building2} label="Cabang" />
            <ExportButton endpoint="master/warehouses" filename="warehouses" icon={Building2} label="Gudang" />
          </div>
        </TabsContent>

        {/* HR & Payroll */}
        <TabsContent value="hr">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <ExportButton endpoint="hr/employees" filename="employees" icon={Users} label="Karyawan" />
            <ExportButton endpoint="hr/jabatan" filename="jabatan" icon={Database} label="Jabatan" />
            <ExportButton endpoint="hr/shifts" filename="shifts" icon={Calendar} label="Shift" />
            <ExportButton endpoint="hr/attendance" filename="attendance" icon={Calendar} label="Absensi" />
            <ExportButton endpoint="hr/payroll" filename="payroll" icon={Wallet} label="Payroll" />
            <ExportButton endpoint="hr/leaves" filename="leaves" icon={Calendar} label="Pengajuan Cuti" />
            <ExportButton endpoint="hr/overtime" filename="overtime" icon={Calendar} label="Pengajuan Lembur" />
          </div>
        </TabsContent>

        {/* KPI */}
        <TabsContent value="kpi">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <ExportButton endpoint="kpi/templates" filename="kpi_templates" icon={ClipboardList} label="Template KPI" />
            <ExportButton endpoint="kpi/targets" filename="kpi_targets" icon={Trophy} label="Target KPI" />
            <ExportButton endpoint="kpi/submissions" filename="kpi_submissions" icon={CheckCircle} label="Submission KPI" />
            <ExportButton endpoint="kpi/rankings" filename="kpi_rankings" icon={TrendingUp} label="Ranking Data" />
            
            {/* Special ranking exports */}
            <div className="p-3 bg-gradient-to-br from-yellow-900/30 to-amber-900/30 rounded-lg border border-yellow-700/30">
              <div className="flex items-center gap-2 mb-2">
                <Trophy className="h-4 w-4 text-yellow-400" />
                <span className="text-sm font-medium text-yellow-100">Ranking Karyawan</span>
              </div>
              <div className="grid grid-cols-4 gap-1">
                {['xlsx', 'pdf', 'csv', 'json'].map((format) => (
                  <Button
                    key={format}
                    size="sm"
                    variant="outline"
                    className="h-8 text-xs bg-yellow-950/50 border-yellow-700/30"
                    onClick={() => {
                      const url = `${API}/api/export-v2/ranking/employees?format=${format}&month=${selectedMonth}&year=${selectedYear}`;
                      window.open(url, '_blank');
                    }}
                  >
                    {format.toUpperCase()}
                  </Button>
                ))}
              </div>
            </div>
            
            <div className="p-3 bg-gradient-to-br from-blue-900/30 to-cyan-900/30 rounded-lg border border-blue-700/30">
              <div className="flex items-center gap-2 mb-2">
                <Building2 className="h-4 w-4 text-blue-400" />
                <span className="text-sm font-medium text-blue-100">Ranking Cabang</span>
              </div>
              <div className="grid grid-cols-4 gap-1">
                {['xlsx', 'pdf', 'csv', 'json'].map((format) => (
                  <Button
                    key={format}
                    size="sm"
                    variant="outline"
                    className="h-8 text-xs bg-blue-950/50 border-blue-700/30"
                    onClick={() => {
                      const url = `${API}/api/export-v2/ranking/branches?format=${format}&month=${selectedMonth}&year=${selectedYear}`;
                      window.open(url, '_blank');
                    }}
                  >
                    {format.toUpperCase()}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Sales */}
        <TabsContent value="sales">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <ExportButton endpoint="sales/transactions" filename="transactions" icon={ShoppingCart} label="Transaksi" />
            <ExportButton endpoint="sales/setoran" filename="setoran" icon={Wallet} label="Setoran Harian" />
            <ExportButton endpoint="sales/selisih" filename="selisih_kas" icon={AlertCircle} label="Selisih Kas" />
          </div>
        </TabsContent>

        {/* Inventory */}
        <TabsContent value="inventory">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <ExportButton endpoint="inventory/stock" filename="stock" icon={Package} label="Stok Saat Ini" />
            <ExportButton endpoint="inventory/mutations" filename="mutations" icon={ClipboardList} label="Mutasi Stok" />
            <ExportButton endpoint="inventory/opname" filename="opname" icon={ClipboardList} label="Stock Opname" />
          </div>
        </TabsContent>

        {/* Accounting */}
        <TabsContent value="accounting">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <ExportButton endpoint="accounting/journals" filename="journals" icon={FileSpreadsheet} label="Jurnal" />
            <ExportButton endpoint="accounting/kas_masuk" filename="kas_masuk" icon={Wallet} label="Kas Masuk" />
            <ExportButton endpoint="accounting/kas_keluar" filename="kas_keluar" icon={Wallet} label="Kas Keluar" />
          </div>
        </TabsContent>

        {/* Audit & CRM */}
        <TabsContent value="audit">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <ExportButton endpoint="audit/logs" filename="audit_logs" icon={ClipboardList} label="Audit Logs" />
            <ExportButton endpoint="audit/kas" filename="audit_kas" icon={Wallet} label="Audit Kas" />
            <ExportButton endpoint="audit/stock" filename="audit_stock" icon={Package} label="Audit Stok" />
            <ExportButton endpoint="crm/customers" filename="crm_customers" icon={Users} label="CRM Customers" />
            <ExportButton endpoint="crm/complaints" filename="complaints" icon={AlertCircle} label="Komplain" />
            <ExportButton endpoint="crm/prompts" filename="ai_prompts" icon={Database} label="AI Prompts" />
          </div>
        </TabsContent>

        {/* Alerts */}
        <TabsContent value="alerts">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <ExportButton endpoint="alerts/all" filename="all_alerts" icon={Bell} label="Semua Alerts" />
            <ExportButton endpoint="alerts/warroom" filename="warroom_alerts" icon={AlertCircle} label="War Room Alerts" />
            
            {/* Dashboard Summary */}
            <div className="p-3 bg-gradient-to-br from-purple-900/30 to-pink-900/30 rounded-lg border border-purple-700/30">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-purple-400" />
                <span className="text-sm font-medium text-purple-100">Dashboard Summary</span>
              </div>
              <div className="grid grid-cols-2 gap-1">
                {['pdf', 'xlsx'].map((format) => (
                  <Button
                    key={format}
                    size="sm"
                    variant="outline"
                    className="h-8 text-xs bg-purple-950/50 border-purple-700/30"
                    onClick={() => {
                      const url = `${API}/api/export-v2/dashboard/summary?format=${format}`;
                      window.open(url, '_blank');
                    }}
                  >
                    {format.toUpperCase()}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Status */}
      <Card className="bg-[#120a0c]/80 border-green-900/30 mt-4">
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-400" />
            <span className="text-green-400 font-medium">Export System Aktif</span>
            <span className="text-gray-500 text-sm ml-2">
              Semua data dapat di-export ke Excel, PDF, CSV, dan JSON
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdvancedExport;
