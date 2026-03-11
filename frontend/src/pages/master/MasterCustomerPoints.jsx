import React, { useState, useEffect } from 'react';
import { Star, Search, Filter, Download, Users } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MasterCustomerPoints = () => {
  
  const [points, setPoints] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState('');

  useEffect(() => {
    fetchCustomers();
    fetchPoints();
  }, []);

  const fetchCustomers = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/api/customers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCustomers(res.data.items || res.data || []);
    } catch (err) {
      console.error('Error fetching customers:', err);
    }
  };

  const fetchPoints = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = selectedCustomer ? { customer_id: selectedCustomer } : {};
      const res = await axios.get(`${API_URL}/api/sales/points`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });
      setPoints(res.data.items || res.data || []);
    } catch (err) {
      console.error('Error fetching points:', err);
      setPoints([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPoints();
  }, [selectedCustomer]);

  // Calculate total points per customer
  const customerPointSummary = customers.map(c => {
    const customerPoints = points.filter(p => p.customer_id === c.id);
    const total = customerPoints.reduce((sum, p) => sum + (p.points || 0), 0);
    return { ...c, total_points: total, transaction_count: customerPoints.length };
  }).filter(c => c.total_points > 0 || search);

  const filteredData = customerPointSummary.filter(c =>
    c.name?.toLowerCase().includes(search.toLowerCase()) ||
    c.code?.toLowerCase().includes(search.toLowerCase())
  );

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('id-ID', {
      day: '2-digit', month: 'short', year: 'numeric'
    });
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('id-ID').format(num || 0);
  };

  return (
    <div className="p-6" data-testid="master-customer-points">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Star className="w-6 h-6 text-yellow-500" />
          Point Pelanggan
        </h1>
        <Button variant="outline" className="border-gray-600">
          <Download className="w-4 h-4 mr-2" /> Export
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 rounded-lg p-4">
          <p className="text-yellow-100 text-sm">Total Member</p>
          <p className="text-2xl font-bold text-white">{customers.filter(c => c.is_member).length}</p>
        </div>
        <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-lg p-4">
          <p className="text-green-100 text-sm">Total Point Beredar</p>
          <p className="text-2xl font-bold text-white">{formatNumber(points.reduce((s, p) => s + (p.points || 0), 0))}</p>
        </div>
        <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg p-4">
          <p className="text-blue-100 text-sm">Point Terpakai</p>
          <p className="text-2xl font-bold text-white">{formatNumber(points.filter(p => p.points < 0).reduce((s, p) => s + Math.abs(p.points || 0), 0))}</p>
        </div>
        <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg p-4">
          <p className="text-purple-100 text-sm">Transaksi Point</p>
          <p className="text-2xl font-bold text-white">{formatNumber(points.length)}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 mb-6">
        <div className="p-4 flex gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Cari pelanggan..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-gray-900 border-gray-700"
            />
          </div>
          <Select value={selectedCustomer || "all"} onValueChange={(v) => setSelectedCustomer(v === "all" ? "" : v)}>
            <SelectTrigger className="w-64 bg-gray-900 border-gray-700">
              <SelectValue placeholder="Semua Pelanggan" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Semua Pelanggan</SelectItem>
              {customers.map(c => (
                <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Customer Points Table */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="p-4 border-b border-gray-700">
          <h2 className="font-semibold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-yellow-500" />
            Daftar Point Pelanggan
          </h2>
        </div>
        <table className="w-full">
          <thead className="bg-gray-900 text-gray-400 text-sm">
            <tr>
              <th className="px-4 py-3 text-left">Kode</th>
              <th className="px-4 py-3 text-left">Nama Pelanggan</th>
              <th className="px-4 py-3 text-left">Telepon</th>
              <th className="px-4 py-3 text-right">Total Point</th>
              <th className="px-4 py-3 text-right">Jml Transaksi</th>
              <th className="px-4 py-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="text-white">
            {loading ? (
              <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">Memuat data...</td></tr>
            ) : filteredData.length === 0 ? (
              <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">Tidak ada data point</td></tr>
            ) : (
              filteredData.map((item) => (
                <tr key={item.id} className="border-t border-gray-700 hover:bg-gray-700/50">
                  <td className="px-4 py-3 font-mono text-yellow-400">{item.code}</td>
                  <td className="px-4 py-3">{item.name}</td>
                  <td className="px-4 py-3 text-gray-400">{item.phone || '-'}</td>
                  <td className="px-4 py-3 text-right font-semibold text-green-400">{formatNumber(item.total_points)}</td>
                  <td className="px-4 py-3 text-right">{item.transaction_count}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded text-xs ${item.is_member ? 'bg-green-600' : 'bg-gray-600'}`}>
                      {item.is_member ? 'Member' : 'Non-Member'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Point History Table */}
      {selectedCustomer && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 mt-6">
          <div className="p-4 border-b border-gray-700">
            <h2 className="font-semibold text-white">Riwayat Point</h2>
          </div>
          <table className="w-full">
            <thead className="bg-gray-900 text-gray-400 text-sm">
              <tr>
                <th className="px-4 py-3 text-left">Tanggal</th>
                <th className="px-4 py-3 text-left">Transaksi</th>
                <th className="px-4 py-3 text-right">Point</th>
                <th className="px-4 py-3 text-left">Keterangan</th>
              </tr>
            </thead>
            <tbody className="text-white">
              {points.filter(p => p.customer_id === selectedCustomer).map((item, idx) => (
                <tr key={idx} className="border-t border-gray-700 hover:bg-gray-700/50">
                  <td className="px-4 py-3 text-gray-400">{formatDate(item.date)}</td>
                  <td className="px-4 py-3">{item.transaction_type}</td>
                  <td className={`px-4 py-3 text-right font-semibold ${item.points > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {item.points > 0 ? '+' : ''}{formatNumber(item.points)}
                  </td>
                  <td className="px-4 py-3 text-gray-400">{item.notes || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default MasterCustomerPoints;
