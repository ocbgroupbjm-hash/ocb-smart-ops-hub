import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  AlertTriangle, Bell, CheckCircle, Clock, Eye, RefreshCw,
  Building2, XCircle, AlertCircle, TrendingUp, User, Play,
  MessageSquare, ArrowUp
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const WarRoomAlertPanel = () => {
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [actionNotes, setActionNotes] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [alertsRes, statsRes] = await Promise.all([
        axios.get(`${API}/api/warroom-alerts/active?limit=100`),
        axios.get(`${API}/api/warroom-alerts/stats/summary`)
      ]);
      
      setAlerts(alertsRes.data.alerts || []);
      setStats(statsRes.data);
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchData]);

  const performAction = async (alertId, action) => {
    try {
      await axios.post(`${API}/api/warroom-alerts/${alertId}/action`, {
        action: action,
        notes: actionNotes,
        user_id: '',
        user_name: 'Admin'
      });
      toast.success(`Alert berhasil di-${action}`);
      setActionNotes('');
      setSelectedAlert(null);
      fetchData();
    } catch (err) {
      toast.error('Gagal melakukan aksi');
    }
  };

  const runAutoCheck = async (type) => {
    try {
      let res;
      if (type === 'minus') {
        res = await axios.post(`${API}/api/warroom-alerts/auto/check-minus`);
      } else if (type === 'stock') {
        res = await axios.post(`${API}/api/warroom-alerts/auto/check-stock`);
      } else if (type === 'unreported') {
        res = await axios.post(`${API}/api/warroom-alerts/auto/check-unreported`);
      }
      toast.success(res.data.message);
      fetchData();
    } catch (err) {
      toast.error('Gagal menjalankan auto-check');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'bg-red-600 animate-pulse';
      case 'high': return 'bg-orange-600';
      case 'medium': return 'bg-yellow-600';
      default: return 'bg-gray-600';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'new': return 'bg-red-500';
      case 'acknowledged': return 'bg-blue-500';
      case 'in_progress': return 'bg-yellow-500';
      case 'escalated': return 'bg-purple-500';
      case 'resolved': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'new': return <AlertCircle className="h-4 w-4" />;
      case 'acknowledged': return <Eye className="h-4 w-4" />;
      case 'in_progress': return <Play className="h-4 w-4" />;
      case 'escalated': return <ArrowUp className="h-4 w-4" />;
      case 'resolved': return <CheckCircle className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleString('id-ID', { 
      day: '2-digit', 
      month: 'short', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0608] to-[#1a0a0e] p-4" data-testid="warroom-alert-panel">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
              <Bell className="h-6 w-6 text-red-400 animate-pulse" />
              War Room Alert Panel
            </h1>
            <p className="text-sm text-gray-400">Real-time monitoring & response center</p>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              onClick={fetchData} 
              disabled={loading}
              className="bg-red-900/50 hover:bg-red-800/50"
            >
              <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Summary */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
          <Card className={`${stats.by_priority?.critical > 0 ? 'bg-gradient-to-br from-red-900/50 to-red-950/80 border-red-500/50 animate-pulse' : 'bg-gradient-to-br from-red-900/30 to-red-950/50 border-red-700/30'}`}>
            <CardContent className="p-3 text-center">
              <AlertCircle className="h-6 w-6 mx-auto text-red-400 mb-1" />
              <p className="text-2xl font-bold text-red-400">{stats.by_priority?.critical || 0}</p>
              <p className="text-xs text-red-300">Critical</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-orange-900/30 to-orange-950/50 border-orange-700/30">
            <CardContent className="p-3 text-center">
              <AlertTriangle className="h-6 w-6 mx-auto text-orange-400 mb-1" />
              <p className="text-2xl font-bold text-orange-400">{stats.by_priority?.high || 0}</p>
              <p className="text-xs text-orange-300">High</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-yellow-900/30 to-yellow-950/50 border-yellow-700/30">
            <CardContent className="p-3 text-center">
              <Clock className="h-6 w-6 mx-auto text-yellow-400 mb-1" />
              <p className="text-2xl font-bold text-yellow-400">{stats.by_priority?.medium || 0}</p>
              <p className="text-xs text-yellow-300">Medium</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-blue-900/30 to-blue-950/50 border-blue-700/30">
            <CardContent className="p-3 text-center">
              <Eye className="h-6 w-6 mx-auto text-blue-400 mb-1" />
              <p className="text-2xl font-bold text-blue-400">{stats.by_status?.acknowledged || 0}</p>
              <p className="text-xs text-blue-300">Acknowledged</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-purple-900/30 to-purple-950/50 border-purple-700/30">
            <CardContent className="p-3 text-center">
              <TrendingUp className="h-6 w-6 mx-auto text-purple-400 mb-1" />
              <p className="text-2xl font-bold text-purple-400">{stats.today_count || 0}</p>
              <p className="text-xs text-purple-300">Hari Ini</p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Alert List */}
        <div className="lg:col-span-2">
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-amber-100 flex items-center gap-2">
                  <Bell className="h-5 w-5 text-red-400" />
                  Active Alerts ({stats?.total_active || 0})
                </CardTitle>
                <div className="flex gap-1">
                  <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => runAutoCheck('minus')}>
                    Check Minus
                  </Button>
                  <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => runAutoCheck('stock')}>
                    Check Stok
                  </Button>
                  <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => runAutoCheck('unreported')}>
                    Check Setor
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {alerts.map((alert) => (
                  <div 
                    key={alert.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedAlert?.id === alert.id 
                        ? 'bg-red-900/40 border-red-500/50' 
                        : 'bg-red-950/20 border-red-900/20 hover:bg-red-900/30'
                    } ${alert.priority === 'critical' ? 'animate-pulse' : ''}`}
                    onClick={() => setSelectedAlert(alert)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-2">
                        <div className={`w-2 h-2 rounded-full mt-2 ${getPriorityColor(alert.priority)}`} />
                        <div>
                          <p className="font-medium text-amber-100">{alert.title}</p>
                          <p className="text-xs text-gray-400">{alert.message}</p>
                          {alert.branch_name && (
                            <p className="text-xs text-blue-400 flex items-center gap-1 mt-1">
                              <Building2 className="h-3 w-3" />
                              {alert.branch_name}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <Badge className={getPriorityColor(alert.priority)}>{alert.priority}</Badge>
                        <Badge className={getStatusColor(alert.status)} variant="outline">
                          {getStatusIcon(alert.status)}
                          <span className="ml-1">{alert.status}</span>
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                      <span>{formatTime(alert.created_at)}</span>
                      {alert.notifications_sent?.length > 0 && (
                        <span className="flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          Notif: {alert.notifications_sent.join(', ')}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                
                {alerts.length === 0 && (
                  <div className="text-center py-8">
                    <CheckCircle className="h-12 w-12 mx-auto text-green-500/50 mb-2" />
                    <p className="text-green-400 font-medium">Tidak Ada Alert Aktif</p>
                    <p className="text-xs text-gray-500">Semua operasional berjalan normal</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detail & Actions */}
        <div className="space-y-4">
          {/* Alert Detail */}
          <Card className="bg-[#120a0c]/80 border-blue-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-100 text-sm">Detail Alert</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedAlert ? (
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-400">Title</p>
                    <p className="text-sm font-medium text-amber-100">{selectedAlert.title}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">Message</p>
                    <p className="text-sm text-gray-300">{selectedAlert.message}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <p className="text-xs text-gray-400">Priority</p>
                      <Badge className={getPriorityColor(selectedAlert.priority)}>{selectedAlert.priority}</Badge>
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Status</p>
                      <Badge className={getStatusColor(selectedAlert.status)}>{selectedAlert.status}</Badge>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">Cabang</p>
                    <p className="text-sm text-blue-400">{selectedAlert.branch_name || '-'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">Waktu</p>
                    <p className="text-sm text-gray-300">{formatTime(selectedAlert.created_at)}</p>
                  </div>
                  
                  {selectedAlert.acknowledged_by && (
                    <div>
                      <p className="text-xs text-gray-400">Acknowledged by</p>
                      <p className="text-sm text-green-400">{selectedAlert.acknowledged_by}</p>
                    </div>
                  )}
                  
                  {/* Actions */}
                  <div className="pt-2 border-t border-red-900/30">
                    <p className="text-xs text-gray-400 mb-2">Actions</p>
                    <Input
                      placeholder="Catatan (opsional)..."
                      value={actionNotes}
                      onChange={(e) => setActionNotes(e.target.value)}
                      className="bg-red-950/50 border-red-700/30 mb-2 text-sm"
                    />
                    <div className="grid grid-cols-2 gap-2">
                      {selectedAlert.status === 'new' && (
                        <Button 
                          size="sm" 
                          className="bg-blue-900/50 hover:bg-blue-800/50"
                          onClick={() => performAction(selectedAlert.id, 'acknowledge')}
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          Acknowledge
                        </Button>
                      )}
                      {selectedAlert.status !== 'resolved' && (
                        <>
                          <Button 
                            size="sm" 
                            className="bg-yellow-900/50 hover:bg-yellow-800/50"
                            onClick={() => performAction(selectedAlert.id, 'in_progress')}
                          >
                            <Play className="h-3 w-3 mr-1" />
                            In Progress
                          </Button>
                          <Button 
                            size="sm" 
                            className="bg-purple-900/50 hover:bg-purple-800/50"
                            onClick={() => performAction(selectedAlert.id, 'escalate')}
                          >
                            <ArrowUp className="h-3 w-3 mr-1" />
                            Escalate
                          </Button>
                          <Button 
                            size="sm" 
                            className="bg-green-900/50 hover:bg-green-800/50"
                            onClick={() => performAction(selectedAlert.id, 'resolve')}
                          >
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Resolve
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6">
                  <Eye className="h-10 w-10 mx-auto text-gray-600 mb-2" />
                  <p className="text-sm text-gray-400">Pilih alert untuk melihat detail</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top Affected Branches */}
          {stats?.top_affected_branches?.length > 0 && (
            <Card className="bg-[#120a0c]/80 border-orange-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-orange-400" />
                  Cabang Terdampak
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {stats.top_affected_branches.map((b, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-orange-900/20 rounded">
                      <span className="text-sm text-amber-100">{b.branch}</span>
                      <Badge className="bg-orange-600">{b.count} alerts</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default WarRoomAlertPanel;
