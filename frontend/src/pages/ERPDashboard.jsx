import React, { useState, useEffect } from 'react';
import { 
  BarChart2, Building2, Users, DollarSign, AlertTriangle, TrendingUp,
  Clock, Calendar, CheckCircle, XCircle, Banknote, Activity
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const ERPDashboard = () => {
  const { toast } = useToast();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await api.get('/api/erp/dashboard/summary');
      setData(res.data);
    } catch (err) {
      toast({ title: 'Error', description: 'Gagal memuat dashboard', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const formatRupiah = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[60vh]">
        <Activity className="h-8 w-8 text-amber-400 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="erp-dashboard-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Dashboard ERP</h1>
          <p className="text-gray-400 text-sm">Summary operasional hari ini - {data?.tanggal}</p>
        </div>
        <Button onClick={fetchDashboard} variant="outline" className="border-amber-700/30">
          Refresh
        </Button>
      </div>

      {/* Main KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border-blue-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Building2 className="h-8 w-8 text-blue-400" />
              <div>
                <p className="text-xs text-gray-400">Cabang</p>
                <p className="text-xl font-bold text-blue-400">
                  {data?.cabang?.sudah_setor}/{data?.cabang?.total}
                </p>
                <p className="text-xs text-gray-500">sudah setor</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-900/30 to-green-800/20 border-green-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <DollarSign className="h-8 w-8 text-green-400" />
              <div>
                <p className="text-xs text-gray-400">Penjualan</p>
                <p className="text-xl font-bold text-green-400">{formatRupiah(data?.keuangan?.total_penjualan)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-900/30 to-red-800/20 border-red-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-8 w-8 text-red-400" />
              <div>
                <p className="text-xs text-gray-400">Total Minus</p>
                <p className="text-xl font-bold text-red-400">{formatRupiah(data?.keuangan?.total_minus)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-900/30 to-amber-800/20 border-amber-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Users className="h-8 w-8 text-amber-400" />
              <div>
                <p className="text-xs text-gray-400">Karyawan</p>
                <p className="text-xl font-bold text-amber-400">{data?.karyawan?.total}</p>
                <p className="text-xs text-gray-500">aktif</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-[#0f0a0a] border-red-900/20">
          <CardHeader>
            <CardTitle className="text-lg text-amber-200">Status Setoran</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-green-900/20 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-400" />
                <span className="text-gray-300">Sudah Setor</span>
              </div>
              <span className="text-xl font-bold text-green-400">{data?.cabang?.sudah_setor}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-red-900/20 rounded-lg">
              <div className="flex items-center gap-2">
                <XCircle className="h-5 w-5 text-red-400" />
                <span className="text-gray-300">Belum Setor</span>
              </div>
              <span className="text-xl font-bold text-red-400">{data?.cabang?.belum_setor}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0f0a0a] border-red-900/20">
          <CardHeader>
            <CardTitle className="text-lg text-amber-200">Alerts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-red-900/20 rounded-lg">
              <span className="text-gray-300">Critical Alerts</span>
              <span className="text-xl font-bold text-red-400">{data?.alerts?.critical}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-yellow-900/20 rounded-lg">
              <span className="text-gray-300">Selisih Pending</span>
              <span className="text-xl font-bold text-yellow-400">{data?.selisih_pending}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ERPDashboard;
