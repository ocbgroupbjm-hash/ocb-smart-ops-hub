// OCB TITAN ERP - HR Attendance Dashboard
// Blueprint: SUPER DUPER DEWA
// Dark Theme Enterprise UI

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Clock, Users, UserCheck, UserX, AlertTriangle, Calendar,
  LogIn, LogOut, MapPin, RefreshCw, Search, Filter, Download,
  ChevronLeft, ChevronRight, TrendingUp, TrendingDown
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Check-in Modal Component
const CheckInModal = ({ isOpen, onClose, employees, onSubmit }) => {
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [method, setMethod] = useState('manual');
  const [location, setLocation] = useState('');
  const [notes, setNotes] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedEmployee) {
      toast.error('Pilih karyawan terlebih dahulu');
      return;
    }
    await onSubmit({
      employee_id: selectedEmployee,
      method,
      location,
      notes
    });
    setSelectedEmployee('');
    setLocation('');
    setNotes('');
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md">
        <div className="p-6 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <LogIn className="w-5 h-5 text-green-500" />
            Check-In Karyawan
          </h2>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Karyawan *</label>
            <select
              value={selectedEmployee}
              onChange={(e) => setSelectedEmployee(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
              required
              data-testid="checkin-employee-select"
            >
              <option value="">Pilih Karyawan</option>
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>
                  {emp.employee_id || emp.nik} - {emp.full_name || emp.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-1">Metode</label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
              data-testid="checkin-method-select"
            >
              <option value="manual">Manual</option>
              <option value="fingerprint">Fingerprint</option>
              <option value="face">Face Recognition</option>
              <option value="gps">GPS</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-1">Lokasi</label>
            <Input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Kantor Pusat"
              className="bg-slate-900 border-slate-700 text-white"
              data-testid="checkin-location-input"
            />
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-1">Catatan</label>
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Catatan tambahan..."
              className="bg-slate-900 border-slate-700 text-white"
            />
          </div>
          
          <div className="flex justify-end gap-3 pt-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={onClose}
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              Batal
            </Button>
            <Button 
              type="submit" 
              className="bg-green-600 hover:bg-green-700 text-white"
              data-testid="checkin-submit-btn"
            >
              <LogIn className="w-4 h-4 mr-2" />
              Check-In
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Check-out Modal Component
const CheckOutModal = ({ isOpen, onClose, employees, onSubmit }) => {
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [method, setMethod] = useState('manual');
  const [location, setLocation] = useState('');
  const [overtime, setOvertime] = useState(0);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedEmployee) {
      toast.error('Pilih karyawan terlebih dahulu');
      return;
    }
    await onSubmit({
      employee_id: selectedEmployee,
      method,
      location,
      overtime_hours: parseFloat(overtime) || 0
    });
    setSelectedEmployee('');
    setLocation('');
    setOvertime(0);
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md">
        <div className="p-6 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <LogOut className="w-5 h-5 text-red-500" />
            Check-Out Karyawan
          </h2>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Karyawan *</label>
            <select
              value={selectedEmployee}
              onChange={(e) => setSelectedEmployee(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
              required
              data-testid="checkout-employee-select"
            >
              <option value="">Pilih Karyawan</option>
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>
                  {emp.employee_id || emp.nik} - {emp.full_name || emp.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-1">Metode</label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-white"
            >
              <option value="manual">Manual</option>
              <option value="fingerprint">Fingerprint</option>
              <option value="face">Face Recognition</option>
              <option value="gps">GPS</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-1">Lokasi</label>
            <Input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Kantor Pusat"
              className="bg-slate-900 border-slate-700 text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-1">Jam Lembur</label>
            <Input
              type="number"
              step="0.5"
              min="0"
              value={overtime}
              onChange={(e) => setOvertime(e.target.value)}
              placeholder="0"
              className="bg-slate-900 border-slate-700 text-white"
              data-testid="checkout-overtime-input"
            />
          </div>
          
          <div className="flex justify-end gap-3 pt-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={onClose}
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              Batal
            </Button>
            <Button 
              type="submit" 
              className="bg-red-600 hover:bg-red-700 text-white"
              data-testid="checkout-submit-btn"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Check-Out
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main Component
const HRAttendance = () => {
  const [todaySummary, setTodaySummary] = useState(null);
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCheckIn, setShowCheckIn] = useState(false);
  const [showCheckOut, setShowCheckOut] = useState(false);
  const [dateFilter, setDateFilter] = useState(new Date().toISOString().split('T')[0]);
  
  const token = localStorage.getItem('token');
  
  const fetchTodayAttendance = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/hr/attendance/today`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      
      setTodaySummary(data.summary || {});
      setAttendanceRecords(data.records || []);
    } catch (error) {
      toast.error('Gagal memuat data absensi');
    }
    setLoading(false);
  }, [token]);
  
  const fetchEmployees = async () => {
    try {
      const res = await fetch(`${API_URL}/api/hr/employees?status=active&limit=500`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setEmployees(data.employees || []);
    } catch (error) {
      console.error('Failed to fetch employees');
    }
  };
  
  const fetchShifts = async () => {
    try {
      const res = await fetch(`${API_URL}/api/hr/attendance/shifts`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setShifts(data.shifts || []);
    } catch (error) {
      console.error('Failed to fetch shifts');
    }
  };
  
  useEffect(() => {
    fetchTodayAttendance();
    fetchEmployees();
    fetchShifts();
  }, [fetchTodayAttendance]);
  
  const handleCheckIn = async (formData) => {
    try {
      const res = await fetch(`${API_URL}/api/hr/attendance/checkin`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(`Check-in berhasil: ${data.employee_name} pada ${data.check_in_time}`);
        if (data.is_late) {
          toast.warning(`Terlambat ${data.late_minutes} menit`);
        }
        setShowCheckIn(false);
        fetchTodayAttendance();
      } else {
        toast.error(data.detail || 'Gagal check-in');
      }
    } catch (error) {
      toast.error('Terjadi kesalahan');
    }
  };
  
  const handleCheckOut = async (formData) => {
    try {
      const res = await fetch(`${API_URL}/api/hr/attendance/checkout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(`Check-out berhasil: ${data.employee_name} - ${data.work_hours} jam kerja`);
        setShowCheckOut(false);
        fetchTodayAttendance();
      } else {
        toast.error(data.detail || 'Gagal check-out');
      }
    } catch (error) {
      toast.error('Terjadi kesalahan');
    }
  };
  
  const getAttendanceRate = () => {
    if (!todaySummary || !todaySummary.total_employees) return 0;
    return ((todaySummary.present / todaySummary.total_employees) * 100).toFixed(1);
  };
  
  return (
    <div className="min-h-screen bg-slate-900 p-6" data-testid="hr-attendance-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Clock className="w-8 h-8 text-orange-500" />
          Dashboard Absensi
        </h1>
        <p className="text-slate-400 mt-1">Attendance Management System</p>
      </div>
      
      {/* Today Stats */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Users className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Total Karyawan</p>
              <p className="text-2xl font-bold text-white">{todaySummary?.total_employees || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <UserCheck className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Hadir</p>
              <p className="text-2xl font-bold text-green-400">{todaySummary?.present || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <UserX className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Tidak Hadir</p>
              <p className="text-2xl font-bold text-red-400">{todaySummary?.absent || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Terlambat</p>
              <p className="text-2xl font-bold text-amber-400">{todaySummary?.late || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <TrendingUp className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Rate Kehadiran</p>
              <p className="text-2xl font-bold text-purple-400">{getAttendanceRate()}%</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Toolbar */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button 
              onClick={() => setShowCheckIn(true)}
              className="bg-green-600 hover:bg-green-700 text-white"
              data-testid="checkin-btn"
            >
              <LogIn className="w-4 h-4 mr-2" />
              Check-In
            </Button>
            <Button 
              onClick={() => setShowCheckOut(true)}
              className="bg-red-600 hover:bg-red-700 text-white"
              data-testid="checkout-btn"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Check-Out
            </Button>
            <Button
              onClick={fetchTodayAttendance}
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              data-testid="refresh-attendance-btn"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
          
          <div className="flex items-center gap-3">
            <Input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="bg-slate-900 border-slate-700 text-white w-44"
              data-testid="date-filter"
            />
            <Button
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              data-testid="export-attendance-btn"
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </div>
      
      {/* Shifts Info */}
      {shifts.length > 0 && (
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 mb-6">
          <h3 className="text-white font-medium mb-3 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-orange-500" />
            Jadwal Shift
          </h3>
          <div className="grid grid-cols-4 gap-3">
            {shifts.map(shift => (
              <div key={shift.id} className="bg-slate-900 rounded-lg p-3 border border-slate-700">
                <p className="text-white font-medium">{shift.name}</p>
                <p className="text-sm text-slate-400">
                  {shift.start_time} - {shift.end_time}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {shift.work_hours} jam kerja
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Attendance Table */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h3 className="text-white font-medium">Absensi Hari Ini - {new Date().toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="attendance-table">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">NIK</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Nama</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Departemen</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Check-In</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Check-Out</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Jam Kerja</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Lembur</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-slate-300">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {loading ? (
                <tr>
                  <td colSpan="8" className="px-4 py-8 text-center text-slate-400">
                    Memuat data...
                  </td>
                </tr>
              ) : attendanceRecords.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-4 py-8 text-center text-slate-400">
                    Belum ada data absensi hari ini
                  </td>
                </tr>
              ) : (
                attendanceRecords.map((record) => (
                  <tr 
                    key={record.id} 
                    className="hover:bg-slate-700/30 transition-colors"
                    data-testid={`attendance-row-${record.id}`}
                  >
                    <td className="px-4 py-3 text-sm text-white font-mono">
                      {record.employee_nik || '-'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-white font-medium">
                        {record.employee_name}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {record.department_name || '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {record.check_in_time ? (
                        <div>
                          <span className="text-green-400 font-mono">{record.check_in_time}</span>
                          {record.is_late && (
                            <span className="ml-2 text-xs text-amber-400">
                              (+{record.late_minutes}m)
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {record.check_out_time ? (
                        <span className="text-red-400 font-mono">{record.check_out_time}</span>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center text-white">
                      {record.work_hours ? `${record.work_hours.toFixed(1)}h` : '-'}
                    </td>
                    <td className="px-4 py-3 text-center text-purple-400">
                      {record.overtime_hours ? `${record.overtime_hours}h` : '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {record.is_late ? (
                        <span className="px-2 py-1 text-xs rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
                          Terlambat
                        </span>
                      ) : record.check_in ? (
                        <span className="px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400 border border-green-500/30">
                          Hadir
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs rounded-full bg-slate-500/20 text-slate-400 border border-slate-500/30">
                          Pending
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Modals */}
      <CheckInModal
        isOpen={showCheckIn}
        onClose={() => setShowCheckIn(false)}
        employees={employees}
        onSubmit={handleCheckIn}
      />
      
      <CheckOutModal
        isOpen={showCheckOut}
        onClose={() => setShowCheckOut(false)}
        employees={employees}
        onSubmit={handleCheckOut}
      />
    </div>
  );
};

export default HRAttendance;
