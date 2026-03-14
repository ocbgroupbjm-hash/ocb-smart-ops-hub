import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { AlertCircle, Calendar, Lock, Unlock, DollarSign, RefreshCw, Plus, Check, X, ArrowRightLeft, Shield } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ERPHardening = () => {
  const [activeTab, setActiveTab] = useState('fiscal');
  
  // Fiscal Period State
  const [fiscalPeriods, setFiscalPeriods] = useState([]);
  const [loadingPeriods, setLoadingPeriods] = useState(false);
  const [showCreatePeriod, setShowCreatePeriod] = useState(false);
  const [newPeriod, setNewPeriod] = useState({
    period_name: '',
    start_date: '',
    end_date: '',
    status: 'open',
    notes: ''
  });
  
  // Multi-Currency State
  const [currencies, setCurrencies] = useState([]);
  const [exchangeRates, setExchangeRates] = useState([]);
  const [currentRates, setCurrentRates] = useState({});
  const [loadingCurrencies, setLoadingCurrencies] = useState(false);
  const [showAddRate, setShowAddRate] = useState(false);
  const [newRate, setNewRate] = useState({
    currency_code: '',
    rate_to_base: '',
    effective_date: new Date().toISOString().split('T')[0],
    notes: ''
  });
  
  // Conversion Calculator State
  const [conversionFrom, setConversionFrom] = useState('USD');
  const [conversionTo, setConversionTo] = useState('IDR');
  const [conversionAmount, setConversionAmount] = useState('');
  const [conversionResult, setConversionResult] = useState(null);

  const getToken = () => localStorage.getItem('token');

  // ==================== FISCAL PERIOD FUNCTIONS ====================
  
  const fetchFiscalPeriods = async () => {
    setLoadingPeriods(true);
    try {
      const res = await axios.get(`${API_URL}/api/erp-hardening/fiscal-periods`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      setFiscalPeriods(res.data.items || []);
    } catch (err) {
      toast.error('Gagal memuat periode fiscal');
    } finally {
      setLoadingPeriods(false);
    }
  };

  const createFiscalPeriod = async () => {
    if (!newPeriod.period_name || !newPeriod.start_date || !newPeriod.end_date) {
      toast.error('Lengkapi semua field');
      return;
    }
    try {
      await axios.post(`${API_URL}/api/erp-hardening/fiscal-periods`, newPeriod, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      toast.success('Periode fiscal berhasil dibuat');
      setShowCreatePeriod(false);
      setNewPeriod({ period_name: '', start_date: '', end_date: '', status: 'open', notes: '' });
      fetchFiscalPeriods();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal membuat periode');
    }
  };

  const closeFiscalPeriod = async (periodId, periodName) => {
    if (!window.confirm(`Yakin ingin menutup periode "${periodName}"? Transaksi tidak dapat dibuat/edit setelah ditutup.`)) return;
    try {
      await axios.post(`${API_URL}/api/erp-hardening/fiscal-periods/${periodId}/close`, {}, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      toast.success('Periode berhasil ditutup');
      fetchFiscalPeriods();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal menutup periode');
    }
  };

  const lockFiscalPeriod = async (periodId, periodName) => {
    if (!window.confirm(`PERINGATAN: Mengunci periode "${periodName}" bersifat PERMANEN dan tidak dapat dibatalkan. Lanjutkan?`)) return;
    try {
      await axios.post(`${API_URL}/api/erp-hardening/fiscal-periods/${periodId}/lock`, {}, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      toast.success('Periode berhasil dikunci secara permanen');
      fetchFiscalPeriods();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal mengunci periode');
    }
  };

  // ==================== MULTI-CURRENCY FUNCTIONS ====================

  const fetchCurrencies = async () => {
    setLoadingCurrencies(true);
    try {
      const [currRes, rateRes, currentRes] = await Promise.all([
        axios.get(`${API_URL}/api/erp-hardening/currencies`, {
          headers: { Authorization: `Bearer ${getToken()}` }
        }),
        axios.get(`${API_URL}/api/erp-hardening/exchange-rates`, {
          headers: { Authorization: `Bearer ${getToken()}` }
        }),
        axios.get(`${API_URL}/api/erp-hardening/exchange-rates/current`, {
          headers: { Authorization: `Bearer ${getToken()}` }
        })
      ]);
      setCurrencies(currRes.data.items || []);
      setExchangeRates(rateRes.data.items || []);
      setCurrentRates(currentRes.data.rates || {});
    } catch (err) {
      toast.error('Gagal memuat data mata uang');
    } finally {
      setLoadingCurrencies(false);
    }
  };

  const initializeDefaultCurrencies = async () => {
    try {
      await axios.post(`${API_URL}/api/erp-hardening/currencies/initialize-defaults`, {}, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      toast.success('Mata uang default berhasil diinisialisasi');
      fetchCurrencies();
    } catch (err) {
      toast.error('Gagal menginisialisasi mata uang');
    }
  };

  const createExchangeRate = async () => {
    if (!newRate.currency_code || !newRate.rate_to_base) {
      toast.error('Lengkapi semua field');
      return;
    }
    try {
      await axios.post(`${API_URL}/api/erp-hardening/exchange-rates`, {
        ...newRate,
        rate_to_base: parseFloat(newRate.rate_to_base)
      }, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      toast.success('Kurs berhasil disimpan');
      setShowAddRate(false);
      setNewRate({ currency_code: '', rate_to_base: '', effective_date: new Date().toISOString().split('T')[0], notes: '' });
      fetchCurrencies();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal menyimpan kurs');
    }
  };

  const convertCurrency = async () => {
    if (!conversionAmount) {
      toast.error('Masukkan jumlah');
      return;
    }
    try {
      const res = await axios.post(`${API_URL}/api/erp-hardening/exchange-rates/convert`, null, {
        params: {
          amount: parseFloat(conversionAmount),
          from_currency: conversionFrom,
          to_currency: conversionTo
        },
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      setConversionResult(res.data);
    } catch (err) {
      toast.error('Gagal konversi mata uang');
    }
  };

  useEffect(() => {
    fetchFiscalPeriods();
    fetchCurrencies();
  }, []);

  const getStatusBadge = (status) => {
    const colors = {
      open: 'bg-green-100 text-green-800 border-green-300',
      closed: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      locked: 'bg-red-100 text-red-800 border-red-300'
    };
    const labels = { open: 'Terbuka', closed: 'Ditutup', locked: 'Terkunci' };
    return <Badge className={`${colors[status] || colors.open} border`}>{labels[status] || status}</Badge>;
  };

  const formatCurrency = (amount, currency = 'IDR') => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: currency === 'IDR' ? 0 : 2
    }).format(amount);
  };

  return (
    <div className="p-6 space-y-6" data-testid="erp-hardening-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="w-7 h-7 text-blue-600" />
            ERP Hardening
          </h1>
          <p className="text-gray-500 mt-1">Fiscal Period System & Multi-Currency Management</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
          <TabsTrigger value="fiscal" className="flex items-center gap-2" data-testid="fiscal-tab">
            <Calendar className="w-4 h-4" />
            Periode Fiscal
          </TabsTrigger>
          <TabsTrigger value="currency" className="flex items-center gap-2" data-testid="currency-tab">
            <DollarSign className="w-4 h-4" />
            Multi-Currency
          </TabsTrigger>
        </TabsList>

        {/* ==================== FISCAL PERIOD TAB ==================== */}
        <TabsContent value="fiscal" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Manajemen Periode Fiscal
                </CardTitle>
                <CardDescription>
                  Kelola periode akuntansi. Periode CLOSED/LOCKED mencegah transaksi baru.
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={fetchFiscalPeriods} data-testid="refresh-periods-btn">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Refresh
                </Button>
                <Dialog open={showCreatePeriod} onOpenChange={setShowCreatePeriod}>
                  <DialogTrigger asChild>
                    <Button size="sm" data-testid="create-period-btn">
                      <Plus className="w-4 h-4 mr-2" />
                      Tambah Periode
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Buat Periode Fiscal Baru</DialogTitle>
                      <DialogDescription>
                        Periode fiscal menentukan rentang waktu untuk transaksi akuntansi
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="space-y-2">
                        <Label>Nama Periode</Label>
                        <Input 
                          placeholder="Contoh: Januari 2026"
                          value={newPeriod.period_name}
                          onChange={e => setNewPeriod({...newPeriod, period_name: e.target.value})}
                          data-testid="period-name-input"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Tanggal Mulai</Label>
                          <Input 
                            type="date"
                            value={newPeriod.start_date}
                            onChange={e => setNewPeriod({...newPeriod, start_date: e.target.value})}
                            data-testid="period-start-input"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Tanggal Akhir</Label>
                          <Input 
                            type="date"
                            value={newPeriod.end_date}
                            onChange={e => setNewPeriod({...newPeriod, end_date: e.target.value})}
                            data-testid="period-end-input"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Status</Label>
                        <Select value={newPeriod.status} onValueChange={v => setNewPeriod({...newPeriod, status: v})}>
                          <SelectTrigger data-testid="period-status-select">
                            <SelectValue placeholder="Pilih status" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="open">Terbuka (Open)</SelectItem>
                            <SelectItem value="closed">Ditutup (Closed)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Catatan</Label>
                        <Input 
                          placeholder="Catatan (opsional)"
                          value={newPeriod.notes}
                          onChange={e => setNewPeriod({...newPeriod, notes: e.target.value})}
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setShowCreatePeriod(false)}>Batal</Button>
                      <Button onClick={createFiscalPeriod} data-testid="save-period-btn">Simpan Periode</Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {loadingPeriods ? (
                <div className="text-center py-8 text-gray-500">Memuat...</div>
              ) : fiscalPeriods.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Belum ada periode fiscal</p>
                  <p className="text-sm mt-2">Klik "Tambah Periode" untuk membuat periode baru</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nama Periode</TableHead>
                      <TableHead>Tanggal Mulai</TableHead>
                      <TableHead>Tanggal Akhir</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Catatan</TableHead>
                      <TableHead className="text-right">Aksi</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fiscalPeriods.map(period => (
                      <TableRow key={period.id} data-testid={`period-row-${period.id}`}>
                        <TableCell className="font-medium">{period.period_name}</TableCell>
                        <TableCell>{period.start_date}</TableCell>
                        <TableCell>{period.end_date}</TableCell>
                        <TableCell>{getStatusBadge(period.status)}</TableCell>
                        <TableCell className="text-gray-500 text-sm">{period.notes || '-'}</TableCell>
                        <TableCell className="text-right">
                          {period.status === 'open' && (
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => closeFiscalPeriod(period.id, period.period_name)}
                              className="mr-2"
                              data-testid={`close-period-${period.id}`}
                            >
                              <X className="w-4 h-4 mr-1" />
                              Tutup
                            </Button>
                          )}
                          {period.status === 'closed' && (
                            <Button 
                              variant="destructive" 
                              size="sm" 
                              onClick={() => lockFiscalPeriod(period.id, period.period_name)}
                              data-testid={`lock-period-${period.id}`}
                            >
                              <Lock className="w-4 h-4 mr-1" />
                              Kunci Permanen
                            </Button>
                          )}
                          {period.status === 'locked' && (
                            <Badge variant="outline" className="text-gray-500">
                              <Lock className="w-3 h-3 mr-1" />
                              Terkunci
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* Fiscal Period Rules Card */}
          <Card className="bg-blue-50 border-blue-200">
            <CardHeader>
              <CardTitle className="text-blue-800 flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                Aturan Periode Fiscal
              </CardTitle>
            </CardHeader>
            <CardContent className="text-blue-700 text-sm space-y-2">
              <div className="flex items-start gap-2">
                <Check className="w-4 h-4 mt-0.5 text-green-600" />
                <span><strong>OPEN:</strong> Transaksi dapat dibuat, diedit, dan dihapus</span>
              </div>
              <div className="flex items-start gap-2">
                <X className="w-4 h-4 mt-0.5 text-yellow-600" />
                <span><strong>CLOSED:</strong> Transaksi tidak dapat dibuat/diedit. Dapat dibuka kembali oleh admin.</span>
              </div>
              <div className="flex items-start gap-2">
                <Lock className="w-4 h-4 mt-0.5 text-red-600" />
                <span><strong>LOCKED:</strong> Periode dikunci permanen. Tidak dapat diubah kembali.</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ==================== MULTI-CURRENCY TAB ==================== */}
        <TabsContent value="currency" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Current Exchange Rates */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="w-5 h-5" />
                    Kurs Saat Ini
                  </CardTitle>
                  <CardDescription>Mata uang dasar: IDR (Rupiah)</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={fetchCurrencies} data-testid="refresh-rates-btn">
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                  <Button variant="outline" size="sm" onClick={initializeDefaultCurrencies}>
                    Initialize
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {loadingCurrencies ? (
                  <div className="text-center py-8 text-gray-500">Memuat...</div>
                ) : Object.keys(currentRates).length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <DollarSign className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Belum ada data kurs</p>
                    <Button variant="link" onClick={initializeDefaultCurrencies}>
                      Klik untuk inisialisasi
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {Object.entries(currentRates).map(([code, data]) => (
                      <div key={code} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg" data-testid={`rate-${code}`}>
                        <div className="flex items-center gap-3">
                          <span className="font-mono font-bold text-lg">{data.symbol || code}</span>
                          <div>
                            <p className="font-medium">{code}</p>
                            <p className="text-xs text-gray-500">{data.name}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-mono font-bold text-lg">
                            {formatCurrency(data.rate_to_base, 'IDR')}
                          </p>
                          <p className="text-xs text-gray-500">per 1 {code}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Currency Converter */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ArrowRightLeft className="w-5 h-5" />
                  Konversi Mata Uang
                </CardTitle>
                <CardDescription>Hitung konversi antar mata uang</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Jumlah</Label>
                  <Input 
                    type="number"
                    placeholder="Masukkan jumlah"
                    value={conversionAmount}
                    onChange={e => setConversionAmount(e.target.value)}
                    data-testid="conversion-amount-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Dari</Label>
                    <Select value={conversionFrom} onValueChange={setConversionFrom}>
                      <SelectTrigger data-testid="conversion-from-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="IDR">IDR - Rupiah</SelectItem>
                        <SelectItem value="USD">USD - US Dollar</SelectItem>
                        <SelectItem value="EUR">EUR - Euro</SelectItem>
                        <SelectItem value="SGD">SGD - Singapore Dollar</SelectItem>
                        <SelectItem value="MYR">MYR - Ringgit</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Ke</Label>
                    <Select value={conversionTo} onValueChange={setConversionTo}>
                      <SelectTrigger data-testid="conversion-to-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="IDR">IDR - Rupiah</SelectItem>
                        <SelectItem value="USD">USD - US Dollar</SelectItem>
                        <SelectItem value="EUR">EUR - Euro</SelectItem>
                        <SelectItem value="SGD">SGD - Singapore Dollar</SelectItem>
                        <SelectItem value="MYR">MYR - Ringgit</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button className="w-full" onClick={convertCurrency} data-testid="convert-btn">
                  <ArrowRightLeft className="w-4 h-4 mr-2" />
                  Konversi
                </Button>
                
                {conversionResult && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg" data-testid="conversion-result">
                    <p className="text-center text-2xl font-bold text-green-700">
                      {formatCurrency(conversionResult.original_amount, conversionResult.original_currency)}
                    </p>
                    <p className="text-center text-gray-500">=</p>
                    <p className="text-center text-3xl font-bold text-green-800">
                      {formatCurrency(conversionResult.converted_amount, conversionResult.target_currency)}
                    </p>
                    <p className="text-center text-xs text-gray-500 mt-2">
                      Kurs: 1 {conversionResult.original_currency} = {formatCurrency(conversionResult.from_rate, 'IDR')}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Add Exchange Rate */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Riwayat & Update Kurs</CardTitle>
                <CardDescription>Kelola kurs harian untuk transaksi multi-currency</CardDescription>
              </div>
              <Dialog open={showAddRate} onOpenChange={setShowAddRate}>
                <DialogTrigger asChild>
                  <Button size="sm" data-testid="add-rate-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    Tambah Kurs
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Tambah Kurs Baru</DialogTitle>
                    <DialogDescription>
                      Input kurs terbaru untuk mata uang asing
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label>Mata Uang</Label>
                      <Select value={newRate.currency_code} onValueChange={v => setNewRate({...newRate, currency_code: v})}>
                        <SelectTrigger data-testid="new-rate-currency-select">
                          <SelectValue placeholder="Pilih mata uang" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="USD">USD - US Dollar</SelectItem>
                          <SelectItem value="EUR">EUR - Euro</SelectItem>
                          <SelectItem value="SGD">SGD - Singapore Dollar</SelectItem>
                          <SelectItem value="MYR">MYR - Malaysian Ringgit</SelectItem>
                          <SelectItem value="CNY">CNY - Chinese Yuan</SelectItem>
                          <SelectItem value="JPY">JPY - Japanese Yen</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Kurs ke IDR</Label>
                      <Input 
                        type="number"
                        placeholder="Contoh: 15500"
                        value={newRate.rate_to_base}
                        onChange={e => setNewRate({...newRate, rate_to_base: e.target.value})}
                        data-testid="new-rate-value-input"
                      />
                      <p className="text-xs text-gray-500">1 {newRate.currency_code || 'XXX'} = Rp {newRate.rate_to_base || '...'}</p>
                    </div>
                    <div className="space-y-2">
                      <Label>Tanggal Efektif</Label>
                      <Input 
                        type="date"
                        value={newRate.effective_date}
                        onChange={e => setNewRate({...newRate, effective_date: e.target.value})}
                        data-testid="new-rate-date-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Catatan</Label>
                      <Input 
                        placeholder="Catatan (opsional)"
                        value={newRate.notes}
                        onChange={e => setNewRate({...newRate, notes: e.target.value})}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setShowAddRate(false)}>Batal</Button>
                    <Button onClick={createExchangeRate} data-testid="save-rate-btn">Simpan Kurs</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Mata Uang</TableHead>
                    <TableHead>Kurs ke IDR</TableHead>
                    <TableHead>Tanggal Efektif</TableHead>
                    <TableHead>Catatan</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {exchangeRates.slice(0, 10).map((rate, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-mono font-bold">{rate.currency_code}</TableCell>
                      <TableCell>{formatCurrency(rate.rate_to_base, 'IDR')}</TableCell>
                      <TableCell>{rate.effective_date}</TableCell>
                      <TableCell className="text-gray-500 text-sm">{rate.notes || '-'}</TableCell>
                    </TableRow>
                  ))}
                  {exchangeRates.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-gray-500 py-8">
                        Belum ada data kurs. Klik "Tambah Kurs" untuk menambahkan.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ERPHardening;
