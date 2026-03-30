import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { AlertCircle, Calculator, Receipt, CheckCircle2, XCircle, AlertTriangle, RefreshCw, FileText, Percent } from 'lucide-react';
import { toast } from 'sonner';

import { getApiUrl } from '../utils/apiConfig';
const API_URL = getApiUrl();

const FinancialControl = () => {
  const [activeTab, setActiveTab] = useState('tax');
  
  // Tax State
  const [taxTypes, setTaxTypes] = useState([]);
  const [taxCalcCode, setTaxCalcCode] = useState('PPN');
  const [taxCalcAmount, setTaxCalcAmount] = useState('');
  const [taxCalcInclusive, setTaxCalcInclusive] = useState(false);
  const [taxResult, setTaxResult] = useState(null);
  
  // PPh 21 State
  const [pph21Salary, setPph21Salary] = useState('');
  const [pph21Ptkp, setPph21Ptkp] = useState('TK/0');
  const [pph21Result, setPph21Result] = useState(null);
  
  // Consistency State
  const [consistencyReport, setConsistencyReport] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);
  
  // Journal Templates State
  const [journalTemplates, setJournalTemplates] = useState([]);
  const [journalPreview, setJournalPreview] = useState(null);
  const [previewTemplate, setPreviewTemplate] = useState('sales_cash');
  const [previewAmount, setPreviewAmount] = useState('');
  const [previewTax, setPreviewTax] = useState('');

  const getToken = () => localStorage.getItem('token');

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(amount);
  };

  // Tax Functions
  const fetchTaxTypes = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/tax-engine/tax-types`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      setTaxTypes(res.data.items || []);
    } catch (err) {
      toast.error('Gagal memuat jenis pajak');
    }
  };

  const calculateTax = async () => {
    if (!taxCalcAmount) {
      toast.error('Masukkan jumlah');
      return;
    }
    try {
      const res = await axios.post(`${API_URL}/api/tax-engine/calculate`, {
        tax_code: taxCalcCode,
        base_amount: parseFloat(taxCalcAmount),
        is_inclusive: taxCalcInclusive
      }, { headers: { Authorization: `Bearer ${getToken()}` } });
      setTaxResult(res.data);
    } catch (err) {
      toast.error('Gagal menghitung pajak');
    }
  };

  const calculatePph21 = async () => {
    if (!pph21Salary) {
      toast.error('Masukkan gaji tahunan');
      return;
    }
    try {
      const res = await axios.post(
        `${API_URL}/api/tax-engine/calculate-pph21?gross_salary=${pph21Salary}&ptkp=${pph21Ptkp}`,
        {}, { headers: { Authorization: `Bearer ${getToken()}` } }
      );
      setPph21Result(res.data);
    } catch (err) {
      toast.error('Gagal menghitung PPh 21');
    }
  };

  // Consistency Functions
  const runConsistencyCheck = async () => {
    setLoadingReport(true);
    try {
      const res = await axios.get(`${API_URL}/api/consistency-checker/full-report`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      setConsistencyReport(res.data);
      toast.success('Laporan konsistensi berhasil dibuat');
    } catch (err) {
      toast.error('Gagal menjalankan pengecekan');
    } finally {
      setLoadingReport(false);
    }
  };

  // Journal Functions
  const fetchJournalTemplates = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/auto-journal/templates`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      setJournalTemplates(res.data.items || []);
    } catch (err) {
      toast.error('Gagal memuat template jurnal');
    }
  };

  const previewJournal = async () => {
    if (!previewAmount) {
      toast.error('Masukkan jumlah');
      return;
    }
    try {
      const res = await axios.get(
        `${API_URL}/api/auto-journal/preview/${previewTemplate}?amount=${previewAmount}&tax_amount=${previewTax || 0}`,
        { headers: { Authorization: `Bearer ${getToken()}` } }
      );
      setJournalPreview(res.data);
    } catch (err) {
      toast.error('Gagal preview jurnal');
    }
  };

  useEffect(() => {
    fetchTaxTypes();
    fetchJournalTemplates();
  }, []);

  const getStatusIcon = (status) => {
    if (status === 'pass') return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    if (status === 'warning') return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    return <XCircle className="w-5 h-5 text-red-500" />;
  };

  const getStatusBadge = (status) => {
    const colors = {
      healthy: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      critical: 'bg-red-100 text-red-800'
    };
    return <Badge className={colors[status] || colors.critical}>{status?.toUpperCase()}</Badge>;
  };

  return (
    <div className="p-6 space-y-6" data-testid="financial-control-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Calculator className="w-7 h-7 text-blue-600" />
            Financial Control System
          </h1>
          <p className="text-gray-500 mt-1">Multi Tax Engine, Consistency Checker, Auto Journal</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 lg:w-[600px]">
          <TabsTrigger value="tax" className="flex items-center gap-2" data-testid="tax-tab">
            <Percent className="w-4 h-4" />
            Multi Tax Engine
          </TabsTrigger>
          <TabsTrigger value="consistency" className="flex items-center gap-2" data-testid="consistency-tab">
            <AlertCircle className="w-4 h-4" />
            Consistency Checker
          </TabsTrigger>
          <TabsTrigger value="journal" className="flex items-center gap-2" data-testid="journal-tab">
            <FileText className="w-4 h-4" />
            Auto Journal
          </TabsTrigger>
        </TabsList>

        {/* ==================== TAX TAB ==================== */}
        <TabsContent value="tax" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Tax Calculator */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Receipt className="w-5 h-5" />
                  Kalkulator Pajak
                </CardTitle>
                <CardDescription>Hitung PPN, PPnBM, PPh</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Jenis Pajak</Label>
                  <Select value={taxCalcCode} onValueChange={setTaxCalcCode}>
                    <SelectTrigger data-testid="tax-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {taxTypes.map(t => (
                        <SelectItem key={t.code} value={t.code}>{t.code} - {t.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Jumlah (Rp)</Label>
                  <Input
                    type="number"
                    placeholder="1000000"
                    value={taxCalcAmount}
                    onChange={e => setTaxCalcAmount(e.target.value)}
                    data-testid="tax-amount-input"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="inclusive"
                    checked={taxCalcInclusive}
                    onChange={e => setTaxCalcInclusive(e.target.checked)}
                  />
                  <Label htmlFor="inclusive">Pajak sudah termasuk (inclusive)</Label>
                </div>
                <Button className="w-full" onClick={calculateTax} data-testid="calc-tax-btn">
                  <Calculator className="w-4 h-4 mr-2" />
                  Hitung
                </Button>

                {taxResult && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg space-y-2" data-testid="tax-result">
                    <p className="text-sm text-gray-600">{taxResult.tax_name} ({taxResult.rate}%)</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <span>DPP:</span>
                      <span className="font-mono text-right">{formatCurrency(taxResult.net_amount)}</span>
                      <span>Pajak:</span>
                      <span className="font-mono text-right font-bold text-blue-600">{formatCurrency(taxResult.tax_amount)}</span>
                      <span>Total:</span>
                      <span className="font-mono text-right">{formatCurrency(taxResult.gross_amount)}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* PPh 21 Calculator */}
            <Card>
              <CardHeader>
                <CardTitle>Kalkulator PPh 21</CardTitle>
                <CardDescription>Hitung PPh 21 dengan tarif progresif</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Gaji Tahunan (Rp)</Label>
                  <Input
                    type="number"
                    placeholder="120000000"
                    value={pph21Salary}
                    onChange={e => setPph21Salary(e.target.value)}
                    data-testid="pph21-salary-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Status PTKP</Label>
                  <Select value={pph21Ptkp} onValueChange={setPph21Ptkp}>
                    <SelectTrigger data-testid="ptkp-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="TK/0">TK/0 - Tidak Kawin</SelectItem>
                      <SelectItem value="TK/1">TK/1 - Tidak Kawin + 1 Tanggungan</SelectItem>
                      <SelectItem value="K/0">K/0 - Kawin</SelectItem>
                      <SelectItem value="K/1">K/1 - Kawin + 1 Tanggungan</SelectItem>
                      <SelectItem value="K/2">K/2 - Kawin + 2 Tanggungan</SelectItem>
                      <SelectItem value="K/3">K/3 - Kawin + 3 Tanggungan</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button className="w-full" onClick={calculatePph21} data-testid="calc-pph21-btn">
                  <Calculator className="w-4 h-4 mr-2" />
                  Hitung PPh 21
                </Button>

                {pph21Result && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg space-y-2" data-testid="pph21-result">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <span>Gaji Tahunan:</span>
                      <span className="font-mono text-right">{formatCurrency(pph21Result.gross_salary)}</span>
                      <span>PTKP ({pph21Result.ptkp_status}):</span>
                      <span className="font-mono text-right">{formatCurrency(pph21Result.ptkp_amount)}</span>
                      <span>PKP:</span>
                      <span className="font-mono text-right">{formatCurrency(pph21Result.pkp)}</span>
                      <span className="font-bold">PPh 21 Tahunan:</span>
                      <span className="font-mono text-right font-bold text-green-600">{formatCurrency(pph21Result.annual_tax)}</span>
                      <span className="font-bold">PPh 21 Bulanan:</span>
                      <span className="font-mono text-right font-bold text-green-600">{formatCurrency(pph21Result.monthly_tax)}</span>
                      <span>Tarif Efektif:</span>
                      <span className="font-mono text-right">{pph21Result.effective_rate}%</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Tax Types Table */}
          <Card>
            <CardHeader>
              <CardTitle>Jenis Pajak yang Didukung</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Kode</TableHead>
                    <TableHead>Nama</TableHead>
                    <TableHead>Tarif Default</TableHead>
                    <TableHead>Kategori</TableHead>
                    <TableHead>Keterangan</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {taxTypes.map(tax => (
                    <TableRow key={tax.code}>
                      <TableCell className="font-mono font-bold">{tax.code}</TableCell>
                      <TableCell>{tax.name}</TableCell>
                      <TableCell>{tax.default_rate}%</TableCell>
                      <TableCell><Badge variant="outline">{tax.category}</Badge></TableCell>
                      <TableCell className="text-gray-500 text-sm">{tax.description}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ==================== CONSISTENCY TAB ==================== */}
        <TabsContent value="consistency" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  Financial Consistency Checker
                </CardTitle>
                <CardDescription>Validasi integritas data keuangan</CardDescription>
              </div>
              <Button onClick={runConsistencyCheck} disabled={loadingReport} data-testid="run-check-btn">
                <RefreshCw className={`w-4 h-4 mr-2 ${loadingReport ? 'animate-spin' : ''}`} />
                {loadingReport ? 'Memeriksa...' : 'Jalankan Pengecekan'}
              </Button>
            </CardHeader>
            <CardContent>
              {!consistencyReport ? (
                <div className="text-center py-12 text-gray-500">
                  <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Klik "Jalankan Pengecekan" untuk memeriksa konsistensi data</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-500">Status Keseluruhan</p>
                      <p className="text-lg font-bold">{getStatusBadge(consistencyReport.overall_status)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">Summary</p>
                      <p className="text-sm">
                        <span className="text-green-600 font-bold">{consistencyReport.summary?.passed}</span> Pass |{' '}
                        <span className="text-yellow-600 font-bold">{consistencyReport.summary?.warnings}</span> Warning |{' '}
                        <span className="text-red-600 font-bold">{consistencyReport.summary?.failed}</span> Fail
                      </p>
                    </div>
                  </div>

                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">Status</TableHead>
                        <TableHead>Pengecekan</TableHead>
                        <TableHead>Hasil</TableHead>
                        <TableHead>Detail</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {consistencyReport.checks?.map((check, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{getStatusIcon(check.status)}</TableCell>
                          <TableCell className="font-medium">{check.check_type}</TableCell>
                          <TableCell>{check.message}</TableCell>
                          <TableCell className="text-sm text-gray-500">
                            {check.details && (
                              <span>
                                {check.details.checked_journals && `${check.details.checked_journals} jurnal diperiksa`}
                                {check.details.difference !== undefined && `Selisih: ${formatCurrency(check.details.difference)}`}
                              </span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ==================== JOURNAL TAB ==================== */}
        <TabsContent value="journal" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Journal Preview */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Preview Jurnal Otomatis
                </CardTitle>
                <CardDescription>Lihat preview entri jurnal sebelum posting</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Template Jurnal</Label>
                  <Select value={previewTemplate} onValueChange={setPreviewTemplate}>
                    <SelectTrigger data-testid="template-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {journalTemplates.map(t => (
                        <SelectItem key={t.code} value={t.code}>{t.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Jumlah (Rp)</Label>
                    <Input
                      type="number"
                      placeholder="1000000"
                      value={previewAmount}
                      onChange={e => setPreviewAmount(e.target.value)}
                      data-testid="preview-amount-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Pajak (Rp)</Label>
                    <Input
                      type="number"
                      placeholder="110000"
                      value={previewTax}
                      onChange={e => setPreviewTax(e.target.value)}
                      data-testid="preview-tax-input"
                    />
                  </div>
                </div>
                <Button className="w-full" onClick={previewJournal} data-testid="preview-btn">
                  <FileText className="w-4 h-4 mr-2" />
                  Preview Jurnal
                </Button>

                {journalPreview && (
                  <div className="mt-4 p-4 bg-slate-800/50 rounded-lg" data-testid="journal-preview">
                    <p className="font-medium mb-2">{journalPreview.template_name}</p>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Akun</TableHead>
                          <TableHead className="text-right">Debit</TableHead>
                          <TableHead className="text-right">Kredit</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {journalPreview.entries?.map((e, idx) => (
                          <TableRow key={idx}>
                            <TableCell>
                              <span className="font-mono text-xs">{e.account_code}</span>
                              <span className="ml-2">{e.account_name}</span>
                            </TableCell>
                            <TableCell className="text-right font-mono">{e.debit > 0 ? formatCurrency(e.debit) : '-'}</TableCell>
                            <TableCell className="text-right font-mono">{e.credit > 0 ? formatCurrency(e.credit) : '-'}</TableCell>
                          </TableRow>
                        ))}
                        <TableRow className="font-bold bg-slate-700/50">
                          <TableCell>TOTAL</TableCell>
                          <TableCell className="text-right font-mono">{formatCurrency(journalPreview.total_debit)}</TableCell>
                          <TableCell className="text-right font-mono">{formatCurrency(journalPreview.total_credit)}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                    <div className="mt-2 text-center">
                      <Badge className={journalPreview.is_balanced ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                        {journalPreview.is_balanced ? '✓ Balanced' : '✗ Not Balanced'}
                      </Badge>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Template List */}
            <Card>
              <CardHeader>
                <CardTitle>Template Jurnal Tersedia</CardTitle>
                <CardDescription>21 template untuk berbagai transaksi</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-[500px] overflow-y-auto">
                  {['sales', 'purchase', 'ar_ap', 'inventory', 'cash_bank'].map(cat => (
                    <div key={cat}>
                      <h4 className="font-medium text-sm text-gray-500 uppercase mb-2">{cat.replace('_', ' / ')}</h4>
                      <div className="space-y-1">
                        {journalTemplates.filter(t => t.code.startsWith(cat.split('_')[0])).map(t => (
                          <div key={t.code} className="p-2 bg-slate-800/50 rounded text-sm">
                            <span className="font-mono text-xs text-gray-500">{t.code}</span>
                            <span className="ml-2">{t.name}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default FinancialControl;
