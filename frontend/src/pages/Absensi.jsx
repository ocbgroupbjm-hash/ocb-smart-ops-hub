import React, { useState, useEffect } from 'react';
import { 
  Fingerprint, MapPin, Clock, Camera, CheckCircle, XCircle,
  Calendar, Building2, User, AlertTriangle, LogIn, LogOut
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const Absensi = () => {
  const { toast } = useToast();
  const [attendance, setAttendance] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [branches, setBranches] = useState([]);
  const [employees, setEmployees] = useState([]);
  
  // Filters
  const [tanggal, setTanggal] = useState(new Date().toISOString().split('T')[0]);
  const [filterBranch, setFilterBranch] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  
  // Check-in state
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [location, setLocation] = useState({ lat: 0, lng: 0, address: '' });
  const [gettingLocation, setGettingLocation] = useState(false);
  const [checkingIn, setCheckingIn] = useState(false);

  useEffect(() => {
    fetchData();
    fetchBranches();
    fetchEmployees();
    fetchDailySummary();
  }, [tanggal, filterBranch, filterStatus]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append('tanggal', tanggal);
      if (filterBranch !== 'all') params.append('branch_id', filterBranch);
      if (filterStatus !== 'all') params.append('status', filterStatus);
      
      const res = await api.get(`/api/attendance/list?${params.toString()}`);
      setAttendance(res.data.attendance || []);
      setSummary(res.data.summary || {});
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat data absensi', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const fetchDailySummary = async () => {
    try {
      const res = await api.get(`/api/attendance/summary/daily?tanggal=${tanggal}`);
      setSummary(res.data.summary || {});
    } catch (err) {
      console.error('Error fetching summary:', err);
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

  const fetchEmployees = async () => {
    try {
      const res = await api.get('/api/erp/employees');
      setEmployees(res.data.employees || []);
    } catch (err) {
      console.error('Error fetching employees:', err);
    }
  };

  const getLocation = () => {
    setGettingLocation(true);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            address: `${position.coords.latitude.toFixed(6)}, ${position.coords.longitude.toFixed(6)}`
          });
          setGettingLocation(false);
          toast({ title: 'Sukses', description: 'Lokasi berhasil didapatkan' });
        },
        (error) => {
          setGettingLocation(false);
          toast({ title: 'Error', description: 'Gagal mendapatkan lokasi: ' + error.message, variant: 'destructive' });
        },
        { enableHighAccuracy: true }
      );
    } else {
      setGettingLocation(false);
      toast({ title: 'Error', description: 'Browser tidak support geolocation', variant: 'destructive' });
    }
  };

  const handleCheckIn = async () => {
    if (!selectedEmployee) {
      toast({ title: 'Error', description: 'Pilih karyawan terlebih dahulu', variant: 'destructive' });
      return;
    }
    if (!location.lat) {
      toast({ title: 'Error', description: 'Dapatkan lokasi terlebih dahulu', variant: 'destructive' });
      return;
    }

    const emp = employees.find(e => e.id === selectedEmployee);
    if (!emp) return;

    setCheckingIn(true);
    try {
      const res = await api.post('/api/attendance/check-in', {
        employee_id: emp.id,
        employee_nik: emp.nik,
        employee_name: emp.name,
        jabatan: emp.jabatan_name || '',
        branch_id: emp.branch_id || '',
        branch_name: emp.branch_name || '',
        latitude: location.lat,
        longitude: location.lng,
        address: location.address,
        device: navigator.userAgent
      });

      toast({ 
        title: 'Check-in Berhasil', 
        description: `${emp.name} - ${res.data.status === 'telat' ? `Telat ${res.data.telat_menit} menit` : 'Tepat waktu'}`
      });
      
      fetchData();
      setSelectedEmployee('');
      setLocation({ lat: 0, lng: 0, address: '' });
    } catch (err) {
      toast({ 
        title: 'Error', 
        description: err.response?.data?.detail || 'Gagal check-in', 
        variant: 'destructive' 
      });
    } finally {
      setCheckingIn(false);
    }
  };

  const handleCheckOut = async (empId) => {
    if (!location.lat) {
      toast({ title: 'Error', description: 'Dapatkan lokasi terlebih dahulu', variant: 'destructive' });
      return;
    }

    try {
      const res = await api.post('/api/attendance/check-out', {
        employee_id: empId,
        latitude: location.lat,
        longitude: location.lng,
        address: location.address,
        device: navigator.userAgent
      });

      toast({ 
        title: 'Check-out Berhasil', 
        description: `Total jam kerja: ${res.data.total_jam_kerja} jam`
      });
      
      fetchData();
    } catch (err) {
      toast({ 
        title: 'Error', 
        description: err.response?.data?.detail || 'Gagal check-out', 
        variant: 'destructive' 
      });
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      hadir: { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Hadir' },
      telat: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Telat' },
      alpha: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Alpha' },
      izin: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Izin' },
      cuti: { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'Cuti' },
      sakit: { bg: 'bg-orange-500/20', text: 'text-orange-400', label: 'Sakit' }
    };
    const badge = badges[status] || badges.alpha;
    return <span className={`px-2 py-1 text-xs rounded-full ${badge.bg} ${badge.text}`}>{badge.label}</span>;
  };

  return (
    <div className="p-6 space-y-6" data-testid="absensi-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-amber-100">Absensi Karyawan</h1>
        <p className="text-gray-400 text-sm">Check-in/out dengan GPS dan selfie</p>
      </div>

      {/* Quick Check-in Card */}
      <Card className="bg-gradient-to-br from-green-900/20 to-green-800/10 border-green-700/30">
        <CardHeader>
          <CardTitle className="text-lg text-green-400 flex items-center gap-2">
            <Fingerprint className="h-5 w-5" /> Quick Check-in
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-gray-400">Pilih Karyawan</label>
              <Select value={selectedEmployee} onValueChange={setSelectedEmployee}>
                <SelectTrigger className="bg-red-950/30 border-red-900/30">
                  <SelectValue placeholder="Pilih Karyawan" />
                </SelectTrigger>
                <SelectContent>
                  {employees.map(e => (
                    <SelectItem key={e.id} value={e.id}>
                      {e.name} ({e.nik})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-gray-400">Lokasi GPS</label>
              <div className="flex gap-2">
                <Input
                  value={location.address}
                  readOnly
                  placeholder="Klik tombol lokasi"
                  className="bg-red-950/30 border-red-900/30 flex-1"
                />
                <Button 
                  type="button"
                  variant="outline"
                  onClick={getLocation}
                  disabled={gettingLocation}
                  className="border-green-700/30"
                >
                  <MapPin className={`h-4 w-4 ${gettingLocation ? 'animate-pulse' : ''}`} />
                </Button>
              </div>
            </div>
            <div className="flex items-end">
              <Button 
                onClick={handleCheckIn}
                disabled={!selectedEmployee || !location.lat || checkingIn}
                className="w-full bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600"
              >
                <LogIn className="h-4 w-4 mr-2" />
                {checkingIn ? 'Processing...' : 'Check-in'}
              </Button>
            </div>
          </div>
          {location.lat !== 0 && (
            <div className="text-xs text-gray-400">
              Koordinat: {location.lat.toFixed(6)}, {location.lng.toFixed(6)}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <Card className="bg-gradient-to-br from-green-900/30 to-green-800/20 border-green-700/30">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-green-400">{summary.hadir || 0}</p>
            <p className="text-xs text-gray-400">Hadir</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-yellow-900/30 to-yellow-800/20 border-yellow-700/30">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-yellow-400">{summary.telat || 0}</p>
            <p className="text-xs text-gray-400">Telat</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-red-900/30 to-red-800/20 border-red-700/30">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-red-400">{summary.alpha || 0}</p>
            <p className="text-xs text-gray-400">Alpha</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border-blue-700/30">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-blue-400">{summary.izin || 0}</p>
            <p className="text-xs text-gray-400">Izin</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border-purple-700/30">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-purple-400">{summary.cuti || 0}</p>
            <p className="text-xs text-gray-400">Cuti</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-orange-900/30 to-orange-800/20 border-orange-700/30">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-orange-400">{summary.sakit || 0}</p>
            <p className="text-xs text-gray-400">Sakit</p>
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
                value={tanggal}
                onChange={(e) => setTanggal(e.target.value)}
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
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-40 bg-red-950/30 border-red-900/30">
                <SelectValue placeholder="Semua Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua Status</SelectItem>
                <SelectItem value="hadir">Hadir</SelectItem>
                <SelectItem value="telat">Telat</SelectItem>
                <SelectItem value="alpha">Alpha</SelectItem>
                <SelectItem value="izin">Izin</SelectItem>
                <SelectItem value="cuti">Cuti</SelectItem>
                <SelectItem value="sakit">Sakit</SelectItem>
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
                  <th className="p-3">Karyawan</th>
                  <th className="p-3">Cabang</th>
                  <th className="p-3 text-center">Status</th>
                  <th className="p-3 text-center">Check-in</th>
                  <th className="p-3 text-center">Check-out</th>
                  <th className="p-3 text-center">Telat</th>
                  <th className="p-3 text-center">Jam Kerja</th>
                  <th className="p-3 text-center">Lokasi Valid</th>
                  <th className="p-3 text-center">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/20">
                {loading ? (
                  <tr>
                    <td colSpan="9" className="p-8 text-center text-gray-400">Loading...</td>
                  </tr>
                ) : attendance.length === 0 ? (
                  <tr>
                    <td colSpan="9" className="p-8 text-center text-gray-400">
                      Tidak ada data absensi untuk tanggal ini
                    </td>
                  </tr>
                ) : attendance.map((item) => (
                  <tr key={item.id} className="hover:bg-red-950/20">
                    <td className="p-3">
                      <div>
                        <p className="text-sm font-medium text-amber-200">{item.employee_name}</p>
                        <p className="text-xs text-gray-500">{item.employee_nik}</p>
                      </div>
                    </td>
                    <td className="p-3 text-sm text-gray-300">{item.branch_name}</td>
                    <td className="p-3 text-center">{getStatusBadge(item.status)}</td>
                    <td className="p-3 text-center text-sm text-gray-300">{item.check_in_time || '-'}</td>
                    <td className="p-3 text-center text-sm text-gray-300">{item.check_out_time || '-'}</td>
                    <td className="p-3 text-center">
                      {item.telat_menit > 0 ? (
                        <span className="text-yellow-400 text-sm">{item.telat_menit} mnt</span>
                      ) : (
                        <span className="text-gray-500 text-sm">-</span>
                      )}
                    </td>
                    <td className="p-3 text-center text-sm text-gray-300">
                      {item.total_jam_kerja ? `${item.total_jam_kerja} jam` : '-'}
                    </td>
                    <td className="p-3 text-center">
                      {item.check_in_valid_location ? (
                        <CheckCircle className="h-4 w-4 text-green-400 mx-auto" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-400 mx-auto" />
                      )}
                    </td>
                    <td className="p-3 text-center">
                      {item.check_in_time && !item.check_out_time && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            if (!location.lat) {
                              getLocation();
                              return;
                            }
                            handleCheckOut(item.employee_id);
                          }}
                          className="text-xs border-red-700/30 text-red-400 hover:bg-red-900/20"
                        >
                          <LogOut className="h-3 w-3 mr-1" /> Out
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Absensi;
