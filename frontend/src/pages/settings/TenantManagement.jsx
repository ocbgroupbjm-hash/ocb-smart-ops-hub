/**
 * OCB TITAN AI - Tenant Management Page
 * =====================================
 * PERINTAH 4: TENANT REGISTRATION FORM
 * 
 * Menu: Pengaturan → Manajemen Tenant → Tambah Tenant
 * Hanya untuk super_admin / owner
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Badge } from '../../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../../components/ui/dialog';
import { AlertCircle, CheckCircle, Database, Building2, UserPlus, RefreshCw, Shield, Activity } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function TenantManagement() {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [creating, setCreating] = useState(false);
  const [syncing, setSyncing] = useState({});
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  
  // Form state
  const [formData, setFormData] = useState({
    business_name: '',
    tenant_id: '',
    database_name: '',
    tenant_type: 'retail',
    status: 'active',
    timezone: 'Asia/Jakarta',
    currency: 'IDR',
    default_branch_name: 'Headquarters',
    default_warehouse_name: 'Gudang Utama',
    admin_name: '',
    admin_email: '',
    admin_password: ''
  });

  const getToken = () => localStorage.getItem('token');

  const fetchTenants = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/tenant/tenants`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch tenants');
      
      const data = await response.json();
      setTenants(data.tenants || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTenants();
  }, []);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Auto-generate tenant_id and database_name from business_name
    if (field === 'business_name') {
      const slugified = value.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');
      setFormData(prev => ({
        ...prev,
        tenant_id: slugified,
        database_name: `ocb_${slugified}`
      }));
    }
  };

  const handleCreateTenant = async () => {
    setCreating(true);
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/api/tenant/tenants`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create tenant');
      }
      
      setSuccessMessage(`Tenant "${formData.business_name}" berhasil dibuat!`);
      setShowCreateDialog(false);
      setFormData({
        business_name: '',
        tenant_id: '',
        database_name: '',
        tenant_type: 'retail',
        status: 'active',
        timezone: 'Asia/Jakarta',
        currency: 'IDR',
        default_branch_name: 'Headquarters',
        default_warehouse_name: 'Gudang Utama',
        admin_name: '',
        admin_email: '',
        admin_password: ''
      });
      fetchTenants();
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleSyncBlueprint = async (tenantId) => {
    setSyncing(prev => ({ ...prev, [tenantId]: true }));
    
    try {
      const response = await fetch(`${API_URL}/api/tenant/tenants/${tenantId}/sync-blueprint`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      
      if (!response.ok) throw new Error('Failed to sync');
      
      setSuccessMessage(`Blueprint synced for ${tenantId}`);
      fetchTenants();
    } catch (err) {
      setError(err.message);
    } finally {
      setSyncing(prev => ({ ...prev, [tenantId]: false }));
    }
  };

  const getHealthBadge = (health) => {
    switch (health) {
      case 'healthy':
        return <Badge className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" /> Healthy</Badge>;
      case 'needs_update':
        return <Badge className="bg-yellow-500"><AlertCircle className="w-3 h-3 mr-1" /> Needs Update</Badge>;
      case 'incomplete':
        return <Badge className="bg-red-500"><AlertCircle className="w-3 h-3 mr-1" /> Incomplete</Badge>;
      default:
        return <Badge className="bg-gray-500">Unknown</Badge>;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-600">Active</Badge>;
      case 'inactive':
        return <Badge className="bg-gray-500">Inactive</Badge>;
      case 'suspended':
        return <Badge className="bg-red-600">Suspended</Badge>;
      default:
        return <Badge className="bg-gray-500">{status}</Badge>;
    }
  };

  return (
    <div className="p-6 space-y-6" data-testid="tenant-management-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Building2 className="w-6 h-6" />
            Manajemen Tenant
          </h1>
          <p className="text-gray-500">Kelola tenant/database bisnis dalam sistem</p>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button data-testid="btn-add-tenant" className="flex items-center gap-2">
              <UserPlus className="w-4 h-4" />
              Tambah Tenant
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                Registrasi Tenant Baru
              </DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded">
                  {error}
                </div>
              )}
              
              {/* Business Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="business_name">Nama Bisnis *</Label>
                  <Input
                    id="business_name"
                    data-testid="input-business-name"
                    value={formData.business_name}
                    onChange={(e) => handleInputChange('business_name', e.target.value)}
                    placeholder="Contoh: Toko Baju Modern"
                  />
                </div>
                <div>
                  <Label htmlFor="tenant_type">Tipe Tenant</Label>
                  <Select value={formData.tenant_type} onValueChange={(v) => handleInputChange('tenant_type', v)}>
                    <SelectTrigger data-testid="select-tenant-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="retail">Retail</SelectItem>
                      <SelectItem value="wholesale">Wholesale</SelectItem>
                      <SelectItem value="hybrid">Hybrid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              {/* Database Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="tenant_id">Tenant ID *</Label>
                  <Input
                    id="tenant_id"
                    data-testid="input-tenant-id"
                    value={formData.tenant_id}
                    onChange={(e) => handleInputChange('tenant_id', e.target.value)}
                    placeholder="toko_baju_modern"
                  />
                  <p className="text-xs text-gray-500 mt-1">Lowercase, alphanumeric, underscore only</p>
                </div>
                <div>
                  <Label htmlFor="database_name">Database Name *</Label>
                  <Input
                    id="database_name"
                    data-testid="input-database-name"
                    value={formData.database_name}
                    onChange={(e) => handleInputChange('database_name', e.target.value)}
                    placeholder="ocb_toko_baju_modern"
                  />
                </div>
              </div>
              
              {/* Regional Settings */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select value={formData.timezone} onValueChange={(v) => handleInputChange('timezone', v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Asia/Jakarta">Asia/Jakarta (WIB)</SelectItem>
                      <SelectItem value="Asia/Makassar">Asia/Makassar (WITA)</SelectItem>
                      <SelectItem value="Asia/Jayapura">Asia/Jayapura (WIT)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="currency">Currency</Label>
                  <Select value={formData.currency} onValueChange={(v) => handleInputChange('currency', v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="IDR">IDR - Rupiah</SelectItem>
                      <SelectItem value="USD">USD - Dollar</SelectItem>
                      <SelectItem value="SGD">SGD - Singapore Dollar</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="status">Status</Label>
                  <Select value={formData.status} onValueChange={(v) => handleInputChange('status', v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              {/* Branch Settings */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="default_branch_name">Nama Cabang Default</Label>
                  <Input
                    id="default_branch_name"
                    value={formData.default_branch_name}
                    onChange={(e) => handleInputChange('default_branch_name', e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="default_warehouse_name">Nama Gudang Default</Label>
                  <Input
                    id="default_warehouse_name"
                    value={formData.default_warehouse_name}
                    onChange={(e) => handleInputChange('default_warehouse_name', e.target.value)}
                  />
                </div>
              </div>
              
              {/* Admin User */}
              <div className="border-t pt-4 mt-4">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Admin User
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="admin_name">Nama Admin *</Label>
                    <Input
                      id="admin_name"
                      data-testid="input-admin-name"
                      value={formData.admin_name}
                      onChange={(e) => handleInputChange('admin_name', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="admin_email">Email Admin *</Label>
                    <Input
                      id="admin_email"
                      type="email"
                      data-testid="input-admin-email"
                      value={formData.admin_email}
                      onChange={(e) => handleInputChange('admin_email', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="admin_password">Password Admin *</Label>
                    <Input
                      id="admin_password"
                      type="password"
                      data-testid="input-admin-password"
                      value={formData.admin_password}
                      onChange={(e) => handleInputChange('admin_password', e.target.value)}
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Batal
              </Button>
              <Button 
                data-testid="btn-submit-tenant"
                onClick={handleCreateTenant} 
                disabled={creating || !formData.business_name || !formData.admin_email || !formData.admin_password}
              >
                {creating ? 'Membuat...' : 'Buat Tenant'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          {successMessage}
          <button onClick={() => setSuccessMessage('')} className="ml-auto">×</button>
        </div>
      )}

      {/* Tenant List */}
      <div className="grid gap-4">
        {loading ? (
          <Card>
            <CardContent className="p-6 text-center">
              Loading tenants...
            </CardContent>
          </Card>
        ) : tenants.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center text-gray-500">
              Belum ada tenant terdaftar
            </CardContent>
          </Card>
        ) : (
          tenants.map((tenant) => (
            <Card key={tenant.database} data-testid={`tenant-card-${tenant.database}`}>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Database className="w-4 h-4" />
                      {tenant.database}
                    </CardTitle>
                    <CardDescription>
                      Blueprint v{tenant.blueprint_version || 'N/A'}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    {getHealthBadge(tenant.health)}
                    {getStatusBadge(tenant.status)}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-6 gap-4 text-sm mb-4">
                  <div>
                    <span className="text-gray-500">Accounts:</span>
                    <span className="ml-2 font-medium">{tenant.accounts}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Products:</span>
                    <span className="ml-2 font-medium">{tenant.products}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Users:</span>
                    <span className="ml-2 font-medium">{tenant.users}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Roles:</span>
                    <span className="ml-2 font-medium">{tenant.roles}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Branches:</span>
                    <span className="ml-2 font-medium">{tenant.branches}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Settings:</span>
                    <span className="ml-2 font-medium">{tenant.account_settings}</span>
                  </div>
                </div>
                
                {tenant.needs_migration && (
                  <div className="flex justify-end">
                    <Button
                      size="sm"
                      variant="outline"
                      data-testid={`btn-sync-${tenant.database}`}
                      onClick={() => handleSyncBlueprint(tenant.database)}
                      disabled={syncing[tenant.database]}
                      className="flex items-center gap-2"
                    >
                      <RefreshCw className={`w-4 h-4 ${syncing[tenant.database] ? 'animate-spin' : ''}`} />
                      {syncing[tenant.database] ? 'Syncing...' : 'Sync Blueprint'}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
