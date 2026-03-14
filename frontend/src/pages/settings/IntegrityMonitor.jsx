import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { 
  Shield, RefreshCw, AlertTriangle, CheckCircle, XCircle, 
  Database, DollarSign, Package, Activity, Clock, Download,
  HardDrive, Zap, Server
} from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

const IntegrityMonitorDashboard = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [generating, setGenerating] = useState(false);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/integrity/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setDashboardData(data);
    } catch (err) {
      toast.error('Gagal memuat data integrity');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const generateReport = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/integrity/generate-report`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        toast.success('Report berhasil digenerate');
      }
    } catch (err) {
      toast.error('Gagal generate report');
    } finally {
      setGenerating(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'PASS':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'WARNING':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'FAIL':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      'PASS': 'bg-green-100 text-green-800 border-green-200',
      'WARNING': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'FAIL': 'bg-red-100 text-red-800 border-red-200',
      'HEALTHY': 'bg-green-100 text-green-800 border-green-200',
      'CRITICAL': 'bg-red-100 text-red-800 border-red-200'
    };
    return (
      <Badge className={`${variants[status] || 'bg-slate-700/50 text-slate-300'}`}>
        {status}
      </Badge>
    );
  };

  const getCheckIcon = (checkName) => {
    const icons = {
      'journal_balance': <Database className="w-5 h-5" />,
      'stock_drift': <Package className="w-5 h-5" />,
      'inventory_vs_gl': <DollarSign className="w-5 h-5" />,
      'cash_variance': <DollarSign className="w-5 h-5" />,
      'backup_status': <HardDrive className="w-5 h-5" />,
      'event_queue': <Zap className="w-5 h-5" />,
      'system_health': <Server className="w-5 h-5" />
    };
    return icons[checkName] || <Activity className="w-5 h-5" />;
  };

  const formatCheckName = (name) => {
    return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  const formatNumber = (num) => {
    if (typeof num !== 'number') return num;
    return new Intl.NumberFormat('id-ID').format(num);
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-2 text-gray-500">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>Memuat data integrity...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="integrity-monitor-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <Shield className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Integrity Monitor</h1>
            <p className="text-sm text-gray-500">Guard System 6 - Enterprise Hardening</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={fetchDashboard}
            disabled={loading}
            data-testid="refresh-integrity-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            onClick={generateReport}
            disabled={generating}
            data-testid="generate-report-btn"
          >
            <Download className={`w-4 h-4 mr-2 ${generating ? 'animate-spin' : ''}`} />
            Generate Report
          </Button>
        </div>
      </div>

      {/* Overall Status Card */}
      {dashboardData && (
        <Card className={`border-2 ${
          dashboardData.overall_status === 'HEALTHY' ? 'border-green-300 bg-green-50' :
          dashboardData.overall_status === 'WARNING' ? 'border-yellow-300 bg-yellow-50' :
          'border-red-300 bg-red-50'
        }`} data-testid="overall-status-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {dashboardData.overall_status === 'HEALTHY' ? (
                  <CheckCircle className="w-12 h-12 text-green-500" />
                ) : dashboardData.overall_status === 'WARNING' ? (
                  <AlertTriangle className="w-12 h-12 text-yellow-500" />
                ) : (
                  <XCircle className="w-12 h-12 text-red-500" />
                )}
                <div>
                  <h2 className="text-2xl font-bold">
                    System Status: {dashboardData.overall_status}
                  </h2>
                  <p className="text-gray-600">
                    Tenant: {dashboardData.tenant} | 
                    Last check: {new Date(dashboardData.timestamp).toLocaleString('id-ID')}
                  </p>
                </div>
              </div>
              <div className="flex gap-4 text-center">
                <div className="px-4 py-2 bg-slate-800 rounded-lg shadow-sm">
                  <div className="text-2xl font-bold text-green-600">{dashboardData.summary?.passed || 0}</div>
                  <div className="text-xs text-gray-500">Passed</div>
                </div>
                <div className="px-4 py-2 bg-slate-800 rounded-lg shadow-sm">
                  <div className="text-2xl font-bold text-yellow-600">{dashboardData.summary?.warnings || 0}</div>
                  <div className="text-xs text-gray-500">Warnings</div>
                </div>
                <div className="px-4 py-2 bg-slate-800 rounded-lg shadow-sm">
                  <div className="text-2xl font-bold text-red-600">{dashboardData.summary?.failed || 0}</div>
                  <div className="text-xs text-gray-500">Failed</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Checks Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {dashboardData?.checks?.map((check, idx) => (
          <Card key={idx} className="hover:shadow-md transition-shadow" data-testid={`check-card-${check.check}`}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center justify-between text-base">
                <div className="flex items-center gap-2">
                  {getCheckIcon(check.check)}
                  <span>{formatCheckName(check.check)}</span>
                </div>
                {getStatusIcon(check.status)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Status</span>
                  {getStatusBadge(check.status)}
                </div>
                
                {/* Check-specific details */}
                {check.check === 'journal_balance' && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Total Debit</span>
                      <span className="font-medium">Rp {formatNumber(check.total_debit)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Total Credit</span>
                      <span className="font-medium">Rp {formatNumber(check.total_credit)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Difference</span>
                      <span className={`font-medium ${check.difference > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        Rp {formatNumber(check.difference)}
                      </span>
                    </div>
                  </>
                )}
                
                {check.check === 'stock_drift' && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Products Checked</span>
                      <span className="font-medium">{check.products_checked}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Discrepancies</span>
                      <span className={`font-medium ${check.discrepancies_found > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {check.discrepancies_found}
                      </span>
                    </div>
                  </>
                )}
                
                {check.check === 'inventory_vs_gl' && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Inventory Value</span>
                      <span className="font-medium">Rp {formatNumber(check.inventory_value)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">GL Balance</span>
                      <span className="font-medium">Rp {formatNumber(check.gl_balance)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Variance</span>
                      <span className={`font-medium ${Math.abs(check.percentage_diff) > 5 ? 'text-red-600' : 'text-green-600'}`}>
                        {check.percentage_diff}%
                      </span>
                    </div>
                  </>
                )}
                
                {check.check === 'cash_variance' && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Total Shortage</span>
                      <span className="font-medium text-red-600">Rp {formatNumber(Math.abs(check.total_shortage))}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Total Overage</span>
                      <span className="font-medium text-green-600">Rp {formatNumber(check.total_overage)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Pending</span>
                      <span className={`font-medium ${check.pending_discrepancies > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
                        {check.pending_discrepancies}
                      </span>
                    </div>
                  </>
                )}
                
                {check.check === 'backup_status' && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Total Backups</span>
                      <span className="font-medium">{check.backup_count}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Recent Backup</span>
                      <span className={`font-medium ${check.has_recent_backup ? 'text-green-600' : 'text-red-600'}`}>
                        {check.has_recent_backup ? 'Yes' : 'No'}
                      </span>
                    </div>
                    {check.latest_backup && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Size</span>
                        <span className="font-medium">{check.latest_backup.size_mb} MB</span>
                      </div>
                    )}
                  </>
                )}
                
                {check.check === 'event_queue' && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Events (1h)</span>
                      <span className="font-medium">{check.total_events}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Failed</span>
                      <span className={`font-medium ${check.failed_count > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {check.failed_count}
                      </span>
                    </div>
                  </>
                )}
                
                {check.check === 'system_health' && check.counts && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Active Users</span>
                      <span className="font-medium">{check.counts.active_users}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Products</span>
                      <span className="font-medium">{check.counts.products}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Journals</span>
                      <span className="font-medium">{check.counts.posted_journals}</span>
                    </div>
                  </>
                )}
                
                <div className="pt-2 text-xs text-gray-400 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(check.checked_at).toLocaleTimeString('id-ID')}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default IntegrityMonitorDashboard;
