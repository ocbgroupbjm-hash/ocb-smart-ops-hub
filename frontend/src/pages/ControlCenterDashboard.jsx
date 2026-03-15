import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Building2, Server, Database, Shield, Users, 
  Activity, AlertTriangle, CheckCircle, RefreshCw,
  Cpu, HardDrive, Zap, TrendingUp, Clock,
  DollarSign, Package, FileText, Lock, Eye
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const ControlCenterDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [systemHealth, setSystemHealth] = useState(null);
  const [tenants, setTenants] = useState(null);
  const [accounting, setAccounting] = useState(null);
  const [inventory, setInventory] = useState(null);
  const [security, setSecurity] = useState(null);
  const [blueprintStatus, setBlueprintStatus] = useState(null);

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem('token');
    return { headers: { Authorization: `Bearer ${token}` } };
  }, []);

  const fetchAllData = useCallback(async () => {
    setLoading(true);
    try {
      const [healthRes, tenantsRes, accRes, invRes, secRes, bpRes] = await Promise.all([
        axios.get(`${API}/api/control-center/health`, getAuthHeaders()),
        axios.get(`${API}/api/control-center/tenants`, getAuthHeaders()),
        axios.get(`${API}/api/control-center/accounting`, getAuthHeaders()),
        axios.get(`${API}/api/control-center/inventory`, getAuthHeaders()),
        axios.get(`${API}/api/control-center/security`, getAuthHeaders()),
        axios.get(`${API}/api/control-center/blueprint/status`, getAuthHeaders())
      ]);
      
      setSystemHealth(healthRes.data);
      setTenants(tenantsRes.data);
      setAccounting(accRes.data);
      setInventory(invRes.data);
      setSecurity(secRes.data);
      setBlueprintStatus(bpRes.data);
      toast.success('Data refreshed successfully');
    } catch (err) {
      console.error('Error fetching control center data:', err);
      toast.error('Failed to fetch some data');
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchAllData();
    // Auto refresh every 30 seconds
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy': case 'pass': case 'success': return 'bg-green-600';
      case 'warning': case 'degraded': return 'bg-yellow-600';
      case 'critical': case 'fail': case 'failed': return 'bg-red-600';
      default: return 'bg-gray-600';
    }
  };

  const getMetricStatus = (percent) => {
    if (percent < 60) return 'healthy';
    if (percent < 80) return 'warning';
    return 'critical';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', { 
      style: 'currency', 
      currency: 'IDR', 
      maximumFractionDigits: 0 
    }).format(amount || 0);
  };

  // Overview Tab - Summary Cards
  const OverviewTab = () => (
    <div className="space-y-4">
      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="bg-gradient-to-br from-blue-900/30 to-blue-950/50 border-blue-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Building2 className="h-8 w-8 text-blue-400" />
              <div>
                <p className="text-xs text-gray-400">Active Tenants</p>
                <p className="text-2xl font-bold text-blue-100">{tenants?.active || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-900/30 to-green-950/50 border-green-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Activity className="h-8 w-8 text-green-400" />
              <div>
                <p className="text-xs text-gray-400">System Status</p>
                <p className="text-2xl font-bold text-green-100 capitalize">{systemHealth?.status || 'Unknown'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-900/30 to-purple-950/50 border-purple-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <FileText className="h-8 w-8 text-purple-400" />
              <div>
                <p className="text-xs text-gray-400">Total Journals</p>
                <p className="text-2xl font-bold text-purple-100">{accounting?.journal_counts?.total?.toLocaleString() || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-900/30 to-orange-950/50 border-orange-700/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8 text-orange-400" />
              <div>
                <p className="text-xs text-gray-400">Security Events</p>
                <p className="text-2xl font-bold text-orange-100">{security?.security_events || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Blueprint Sync Status */}
      <Card className="bg-[#1E293B] border-[#334155]">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-gray-200 flex items-center gap-2">
            <Lock className="h-5 w-5 text-cyan-400" />
            Blueprint Sync Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-gray-400">Current Version</p>
              <Badge className="bg-cyan-600 text-white">{blueprintStatus?.current_version || 'Unknown'}</Badge>
            </div>
            <div>
              <p className="text-sm text-gray-400">All Synced</p>
              <Badge className={blueprintStatus?.all_synced ? 'bg-green-600' : 'bg-red-600'}>
                {blueprintStatus?.all_synced ? 'Yes' : 'No'}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-gray-400">Synced Count</p>
              <p className="text-xl font-bold text-gray-200">
                {blueprintStatus?.synced_count || 0} / {blueprintStatus?.total_tenants || 0}
              </p>
            </div>
          </div>
          <div className="space-y-2">
            {blueprintStatus?.tenants?.map((tenant, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-[#0F172A] rounded">
                <span className="text-gray-300">{tenant.tenant_name}</span>
                <Badge className={tenant.is_current ? 'bg-green-600' : 'bg-yellow-600'}>
                  {tenant.blueprint_version || 'Unknown'}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* System Metrics */}
      <Card className="bg-[#1E293B] border-[#334155]">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-gray-200 flex items-center gap-2">
            <Server className="h-5 w-5 text-blue-400" />
            System Health Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {/* CPU */}
            <div className="text-center">
              <Cpu className="h-8 w-8 mx-auto text-blue-400 mb-2" />
              <p className="text-xs text-gray-400">CPU Usage</p>
              <p className="text-2xl font-bold text-gray-200">{systemHealth?.metrics?.cpu?.percent?.toFixed(1) || 0}%</p>
              <Badge className={getStatusColor(systemHealth?.metrics?.cpu?.status)}>
                {systemHealth?.metrics?.cpu?.status || 'Unknown'}
              </Badge>
            </div>
            {/* Memory */}
            <div className="text-center">
              <HardDrive className="h-8 w-8 mx-auto text-purple-400 mb-2" />
              <p className="text-xs text-gray-400">Memory</p>
              <p className="text-2xl font-bold text-gray-200">{systemHealth?.metrics?.memory?.percent?.toFixed(1) || 0}%</p>
              <Badge className={getStatusColor(systemHealth?.metrics?.memory?.status)}>
                {systemHealth?.metrics?.memory?.status || 'Unknown'}
              </Badge>
            </div>
            {/* Disk */}
            <div className="text-center">
              <Database className="h-8 w-8 mx-auto text-green-400 mb-2" />
              <p className="text-xs text-gray-400">Disk</p>
              <p className="text-2xl font-bold text-gray-200">{systemHealth?.metrics?.disk?.percent?.toFixed(1) || 0}%</p>
              <Badge className={getStatusColor(systemHealth?.metrics?.disk?.status)}>
                {systemHealth?.metrics?.disk?.status || 'Unknown'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Tenant Overview Tab
  const TenantTab = () => (
    <div className="space-y-4">
      <Card className="bg-[#1E293B] border-[#334155]">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-gray-200 flex items-center gap-2">
            <Building2 className="h-5 w-5 text-blue-400" />
            Tenant Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <p className="text-3xl font-bold text-green-400">{tenants?.active || 0}</p>
              <p className="text-sm text-gray-400">Active</p>
            </div>
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <p className="text-3xl font-bold text-yellow-400">{tenants?.inactive || 0}</p>
              <p className="text-sm text-gray-400">Inactive</p>
            </div>
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <p className="text-3xl font-bold text-purple-400">{tenants?.ai_enabled || 0}</p>
              <p className="text-sm text-gray-400">AI Enabled</p>
            </div>
          </div>
          <div className="space-y-2">
            {tenants?.tenants?.map((tenant, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-[#0F172A] rounded border border-[#334155]">
                <div className="flex items-center gap-3">
                  <Building2 className="h-5 w-5 text-blue-400" />
                  <div>
                    <p className="text-gray-200 font-medium">{tenant.name}</p>
                    <p className="text-xs text-gray-500">{tenant.db_name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={tenant.status === 'active' ? 'bg-green-600' : 'bg-gray-600'}>
                    {tenant.status}
                  </Badge>
                  {tenant.ai_enabled && (
                    <Badge className="bg-purple-600">AI</Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Accounting Balance Tab
  const AccountingTab = () => (
    <div className="space-y-4">
      <Card className="bg-[#1E293B] border-[#334155]">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-gray-200 flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-green-400" />
            Accounting Balance Monitor
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Trial Balance Status */}
          <div className="mb-6 p-4 bg-[#0F172A] rounded">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Trial Balance Status</p>
                <Badge className={accounting?.trial_balance?.is_balanced ? 'bg-green-600' : 'bg-red-600'} size="lg">
                  {accounting?.trial_balance?.is_balanced ? 'BALANCED' : 'UNBALANCED'}
                </Badge>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Total Debit</p>
                <p className="text-lg font-bold text-green-400">{formatCurrency(accounting?.trial_balance?.total_debit)}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Total Credit</p>
                <p className="text-lg font-bold text-red-400">{formatCurrency(accounting?.trial_balance?.total_credit)}</p>
              </div>
            </div>
          </div>

          {/* Journal Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <FileText className="h-8 w-8 mx-auto text-blue-400 mb-2" />
              <p className="text-2xl font-bold text-gray-200">{accounting?.journal_counts?.total?.toLocaleString() || 0}</p>
              <p className="text-sm text-gray-400">Total Journals</p>
            </div>
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <CheckCircle className="h-8 w-8 mx-auto text-green-400 mb-2" />
              <p className="text-2xl font-bold text-gray-200">{accounting?.journal_counts?.posted?.toLocaleString() || 0}</p>
              <p className="text-sm text-gray-400">Posted</p>
            </div>
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <Clock className="h-8 w-8 mx-auto text-yellow-400 mb-2" />
              <p className="text-2xl font-bold text-gray-200">{accounting?.journal_counts?.draft?.toLocaleString() || 0}</p>
              <p className="text-sm text-gray-400">Draft</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Inventory Monitor Tab
  const InventoryTab = () => (
    <div className="space-y-4">
      <Card className="bg-[#1E293B] border-[#334155]">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-gray-200 flex items-center gap-2">
            <Package className="h-5 w-5 text-orange-400" />
            Inventory Monitor
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <p className="text-3xl font-bold text-blue-400">{inventory?.total_products || 0}</p>
              <p className="text-sm text-gray-400">Total Products</p>
            </div>
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <p className="text-3xl font-bold text-yellow-400">{inventory?.low_stock_count || 0}</p>
              <p className="text-sm text-gray-400">Low Stock</p>
            </div>
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <p className="text-3xl font-bold text-red-400">{inventory?.out_of_stock_count || 0}</p>
              <p className="text-sm text-gray-400">Out of Stock</p>
            </div>
          </div>

          {inventory?.low_stock_items?.length > 0 && (
            <div>
              <p className="text-sm text-gray-400 mb-2">Low Stock Items</p>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {inventory.low_stock_items.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-[#0F172A] rounded">
                    <span className="text-gray-300">{item.product_id}</span>
                    <Badge className="bg-yellow-600">{item.quantity} units</Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );

  // Security Center Tab
  const SecurityTab = () => (
    <div className="space-y-4">
      <Card className="bg-[#1E293B] border-[#334155]">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-gray-200 flex items-center gap-2">
            <Shield className="h-5 w-5 text-red-400" />
            Security Center
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <CheckCircle className="h-8 w-8 mx-auto text-green-400 mb-2" />
              <p className="text-2xl font-bold text-gray-200">{security?.login_stats?.successful || 0}</p>
              <p className="text-sm text-gray-400">Successful Logins</p>
            </div>
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <AlertTriangle className="h-8 w-8 mx-auto text-red-400 mb-2" />
              <p className="text-2xl font-bold text-gray-200">{security?.login_stats?.failed || 0}</p>
              <p className="text-sm text-gray-400">Failed Logins</p>
            </div>
            <div className="text-center p-4 bg-[#0F172A] rounded">
              <Shield className="h-8 w-8 mx-auto text-orange-400 mb-2" />
              <p className="text-2xl font-bold text-gray-200">{security?.security_events || 0}</p>
              <p className="text-sm text-gray-400">Security Events</p>
            </div>
          </div>

          {security?.recent_logins?.length > 0 && (
            <div>
              <p className="text-sm text-gray-400 mb-2">Recent Login Activity</p>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {security.recent_logins.slice(0, 10).map((log, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-[#0F172A] rounded">
                    <div>
                      <span className="text-gray-300">{log.user_name || log.user_id}</span>
                      <p className="text-xs text-gray-500">{log.timestamp}</p>
                    </div>
                    <Badge className={log.action === 'login' ? 'bg-green-600' : 'bg-red-600'}>
                      {log.action}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0608] to-[#1a0a0e] p-4" data-testid="control-center-page">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
              <Server className="h-6 w-6 text-cyan-400" />
              Enterprise Control Center
            </h1>
            <p className="text-sm text-gray-400">Multi-tenant monitoring & system governance</p>
          </div>
          <Button 
            onClick={fetchAllData} 
            disabled={loading}
            className="bg-cyan-900/50 hover:bg-cyan-800/50 text-cyan-100"
            data-testid="refresh-control-center"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-[#1E293B] border border-[#334155]">
          <TabsTrigger value="overview" className="data-[state=active]:bg-cyan-900/50">
            <Eye className="h-4 w-4 mr-1" /> Overview
          </TabsTrigger>
          <TabsTrigger value="tenants" className="data-[state=active]:bg-cyan-900/50">
            <Building2 className="h-4 w-4 mr-1" /> Tenants
          </TabsTrigger>
          <TabsTrigger value="accounting" className="data-[state=active]:bg-cyan-900/50">
            <DollarSign className="h-4 w-4 mr-1" /> Accounting
          </TabsTrigger>
          <TabsTrigger value="inventory" className="data-[state=active]:bg-cyan-900/50">
            <Package className="h-4 w-4 mr-1" /> Inventory
          </TabsTrigger>
          <TabsTrigger value="security" className="data-[state=active]:bg-cyan-900/50">
            <Shield className="h-4 w-4 mr-1" /> Security
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <RefreshCw className="h-8 w-8 animate-spin text-cyan-400" />
            </div>
          ) : (
            <OverviewTab />
          )}
        </TabsContent>

        <TabsContent value="tenants">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <RefreshCw className="h-8 w-8 animate-spin text-cyan-400" />
            </div>
          ) : (
            <TenantTab />
          )}
        </TabsContent>

        <TabsContent value="accounting">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <RefreshCw className="h-8 w-8 animate-spin text-cyan-400" />
            </div>
          ) : (
            <AccountingTab />
          )}
        </TabsContent>

        <TabsContent value="inventory">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <RefreshCw className="h-8 w-8 animate-spin text-cyan-400" />
            </div>
          ) : (
            <InventoryTab />
          )}
        </TabsContent>

        <TabsContent value="security">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <RefreshCw className="h-8 w-8 animate-spin text-cyan-400" />
            </div>
          ) : (
            <SecurityTab />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ControlCenterDashboard;
