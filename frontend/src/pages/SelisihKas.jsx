import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, Search, Filter, Calendar, Building2, User,
  CheckCircle, XCircle, Clock, DollarSign, FileText, ArrowUpRight
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const SelisihKas = () => {
  const { toast } = useToast();
  const [selisih, setSelisih] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [branches, setBranches] = useState([]);
  
  // Filters
  const [startDate, setStartDate] = useState(new Date(new Date().setDate(1)).toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [filterBranch, setFilterBranch] = useState('all');
  const [filterJenis, setFilterJenis] = useState('all');
  const [filterResolution, setFilterResolution] = useState('all');
  
  // Modal
  const [showModal, setShowModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [resolution, setResolution] = useState('pending');
  const [resolutionNote, setResolutionNote] = useState('');
  const [isPotongGaji, setIsPotongGaji] = useState(false);
  const [potongGajiMonth, setPotongGajiMonth] = useState('');
  const [potongGajiAmount, setPotongGajiAmount] = useState(0);

  useEffect(() => {
    fetchData();
    fetchBranches();
  }, [startDate, endDate, filterBranch, filterJenis, filterResolution]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append('start_date', startDate);
      params.append('end_date', endDate);
      if (filterBranch !== 'all') params.append('branch_id', filterBranch);
      if (filterJenis !== 'all') params.append('jenis', filterJenis);
      if (filterResolution !== 'all') params.append('resolution', filterResolution);
      
      const res = await api.get(`/api/erp/selisih-kas?${params.toString()}`);
      setSelisih(res.data.selisih || []);
      setSummary(res.data.summary || {});
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat data selisih kas', variant: 'destructive' });
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

  const openResolve = (item) => {
    setSelectedItem(item);
    setResolution(item.resolution || 'pending');
    setResolutionNote(item.resolution_note || '');
    setIsPotongGaji(item.is_potong_gaji || false);
    setPotongGajiMonth(item.potong_gaji_month || '');
    setPotongGajiAmount(item.potong_gaji_amount || item.nominal || 0);
    setShowModal(true);
  };

  const handleResolve = async () => {
    try {
      await api.put(`/api/erp/selisih-kas/${selectedItem.id}/resolve`, {
        resolution,
        resolution_note: resolutionNote,
        is_piutang: resolution === 'piutang_karyawan',
        is_potong_gaji: isPotongGaji,
        potong_gaji_month: potongGajiMonth,
        potong_gaji_amount: potongGajiAmount,
        approved_by_id: 'current-user',
        approved_by_name: 'Admin'
      });
      
      toast({ title: 'Sukses', description: 'Resolusi berhasil disimpan' });
      setShowModal(false);
      fetchData();
    } catch (err) {
      toast({ 
        title: 'Error', 
        description: err.response?.data?.detail || 'Gagal menyimpan resolusi', 
        variant: 'destructive' 
      });
    }
  };

  const getJenisBadge = (jenis) => {
    if (jenis === 'minus') {
      return <span className="px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400">MINUS</span>;
    }
    return <span className="px-2 py-1 text-xs rounded-full bg-blue-500/20 text-blue-400">PLUS</span>;
  };

  const getResolutionBadge = (res) => {
    const badges = {
      pending: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Pending' },
      beban: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Beban Perusahaan' },
      piutang_karyawan: { bg: 'bg-orange-500/20', text: 'text-orange-400', label: 'Piutang Karyawan' },
      potong_gaji: { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'Potong Gaji' },
      pendapatan_lain: { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Pendapatan Lain' },
      koreksi: { bg: 'bg-gray-500/20', text: 'text-gray-400', label: 'Koreksi' },
      closed: { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Closed' }
    };
    const badge = badges[res] || badges.pending;
    return <span className={`px-2 py-1 text-xs rounded-full ${badge.bg} ${badge.text}`}>{badge.label}</span>;
  };

  const formatRupiah = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  };

  return (
    <div className="p-6 space-y-6" data-testid="selisih-kas-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-amber-100">Selisih Kas (Plus/Minus)</h1>
        <p className="text-gray-400 text-sm">Tracking dan resolusi selisih kas harian</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-red-900/30 to-red-800/20 border-red-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-500/20 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Total Minus</p>
                <p className="text-xl font-bold text-red-400">{formatRupiah(summary.total_minus)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border-blue-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <ArrowUpRight className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Total Plus</p>
                <p className="text-xl font-bold text-blue-400">{formatRupiah(summary.total_plus)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-900/30 to-amber-800/20 border-amber-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <DollarSign className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Net Selisih</p>
                <p className={`text-xl font-bold ${(summary.net || 0) < 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {formatRupiah(summary.net)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-900/30 to-yellow-800/20 border-yellow-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-500/20 rounded-lg">
                <Clock className="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Pending</p>
                <p className="text-xl font-bold text-yellow-400">{summary.pending_count || 0}</p>
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
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-40 bg-red-950/30 border-red-900/30"
              />
              <span className="text-gray-400">-</span>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
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
            <Select value={filterJenis} onValueChange={setFilterJenis}>
              <SelectTrigger className="w-32 bg-red-950/30 border-red-900/30">
                <SelectValue placeholder="Jenis" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua</SelectItem>
                <SelectItem value="minus">Minus</SelectItem>
                <SelectItem value="plus">Plus</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterResolution} onValueChange={setFilterResolution}>
              <SelectTrigger className="w-40 bg-red-950/30 border-red-900/30">
                <SelectValue placeholder="Resolusi" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="beban">Beban Perusahaan</SelectItem>
                <SelectItem value="piutang_karyawan">Piutang Karyawan</SelectItem>
                <SelectItem value="potong_gaji">Potong Gaji</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
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
                  <th className="p-3 text-center">Jenis</th>
                  <th className="p-3 text-right">Nominal</th>
                  <th className="p-3 text-center">Resolusi</th>
                  <th className="p-3 text-center">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/20">
                {loading ? (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-gray-400">Loading...</td>
                  </tr>
                ) : selisih.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-gray-400">
                      Tidak ada data selisih kas
                    </td>
                  </tr>
                ) : selisih.map((item) => (
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
                    <td className="p-3 text-center">{getJenisBadge(item.jenis)}</td>
                    <td className={`p-3 text-sm text-right font-bold ${item.jenis === 'minus' ? 'text-red-400' : 'text-blue-400'}`}>
                      {formatRupiah(item.nominal)}
                    </td>
                    <td className="p-3 text-center">{getResolutionBadge(item.resolution)}</td>
                    <td className="p-3">
                      <div className="flex items-center justify-center">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => openResolve(item)}
                          className="text-xs border-amber-700/30 text-amber-400 hover:bg-amber-900/20"
                        >
                          {item.resolution === 'pending' ? 'Resolve' : 'Edit'}
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

      {/* Resolve Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-lg bg-[#0f0a0a] border-red-900/30">
          <DialogHeader>
            <DialogTitle className="text-amber-100">Resolusi Selisih Kas</DialogTitle>
          </DialogHeader>
          
          {selectedItem && (
            <div className="space-y-4">
              {/* Info */}
              <div className="p-3 bg-red-950/30 rounded-lg space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Tanggal:</span>
                  <span className="text-gray-200">{selectedItem.tanggal}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Cabang:</span>
                  <span className="text-gray-200">{selectedItem.branch_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Penjaga:</span>
                  <span className="text-gray-200">{selectedItem.penjaga_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Jenis:</span>
                  {getJenisBadge(selectedItem.jenis)}
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Nominal:</span>
                  <span className={`font-bold ${selectedItem.jenis === 'minus' ? 'text-red-400' : 'text-blue-400'}`}>
                    {formatRupiah(selectedItem.nominal)}
                  </span>
                </div>
              </div>

              {/* Resolution Select */}
              <div>
                <label className="text-xs text-gray-400">Tindakan Resolusi</label>
                <Select value={resolution} onValueChange={setResolution}>
                  <SelectTrigger className="bg-red-950/30 border-red-900/30">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pending (Belum diproses)</SelectItem>
                    {selectedItem.jenis === 'minus' && (
                      <>
                        <SelectItem value="beban">Beban Perusahaan</SelectItem>
                        <SelectItem value="piutang_karyawan">Piutang Karyawan</SelectItem>
                        <SelectItem value="potong_gaji">Potong Gaji</SelectItem>
                        <SelectItem value="koreksi">Koreksi / Error System</SelectItem>
                      </>
                    )}
                    {selectedItem.jenis === 'plus' && (
                      <>
                        <SelectItem value="pendapatan_lain">Pendapatan Lain-lain</SelectItem>
                        <SelectItem value="koreksi">Koreksi / Error System</SelectItem>
                      </>
                    )}
                    <SelectItem value="closed">Closed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Potong Gaji Options */}
              {resolution === 'potong_gaji' && (
                <div className="space-y-3 p-3 bg-purple-900/20 rounded-lg border border-purple-700/30">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={isPotongGaji}
                      onChange={(e) => setIsPotongGaji(e.target.checked)}
                      className="rounded"
                    />
                    <label className="text-sm text-gray-300">Potong dari gaji</label>
                  </div>
                  {isPotongGaji && (
                    <>
                      <div>
                        <label className="text-xs text-gray-400">Periode Gaji</label>
                        <Input
                          type="month"
                          value={potongGajiMonth}
                          onChange={(e) => setPotongGajiMonth(e.target.value)}
                          className="bg-red-950/30 border-red-900/30"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-gray-400">Jumlah Potongan</label>
                        <Input
                          type="number"
                          value={potongGajiAmount}
                          onChange={(e) => setPotongGajiAmount(parseFloat(e.target.value) || 0)}
                          className="bg-red-950/30 border-red-900/30"
                        />
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Note */}
              <div>
                <label className="text-xs text-gray-400">Catatan Resolusi</label>
                <Input
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  className="bg-red-950/30 border-red-900/30"
                  placeholder="Catatan atau alasan..."
                />
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setShowModal(false)}>
                  Batal
                </Button>
                <Button 
                  onClick={handleResolve}
                  className="bg-gradient-to-r from-red-600 to-amber-600"
                >
                  Simpan Resolusi
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SelisihKas;
