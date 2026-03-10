import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { 
  MessageSquare, Bell, Settings, Users, Send, History,
  AlertTriangle, CheckCircle, Plus, Trash2, RefreshCw,
  Phone, User, Shield
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const WhatsAppAlerts = () => {
  const [config, setConfig] = useState(null);
  const [recipients, setRecipients] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [triggers, setTriggers] = useState({});
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Form states
  const [newRecipient, setNewRecipient] = useState({
    name: '',
    phone: '',
    role: 'admin',
    is_active: true,
    alert_types: []
  });
  const [testPhone, setTestPhone] = useState('');
  const [testMessage, setTestMessage] = useState('Test alert dari OCB TITAN AI');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [configRes, recipientsRes, templatesRes, triggersRes, logsRes] = await Promise.all([
        axios.get(`${API}/api/whatsapp-alerts/config`),
        axios.get(`${API}/api/whatsapp-alerts/recipients`),
        axios.get(`${API}/api/whatsapp-alerts/templates`),
        axios.get(`${API}/api/whatsapp-alerts/triggers`),
        axios.get(`${API}/api/whatsapp-alerts/logs?limit=50`)
      ]);
      
      setConfig(configRes.data);
      setRecipients(recipientsRes.data.recipients || []);
      setTemplates(templatesRes.data.templates || []);
      setTriggers(triggersRes.data.triggers || {});
      setLogs(logsRes.data.logs || []);
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    try {
      await axios.put(`${API}/api/whatsapp-alerts/config`, config);
      toast.success('Konfigurasi berhasil disimpan');
    } catch (err) {
      toast.error('Gagal menyimpan konfigurasi');
    }
  };

  const addRecipient = async () => {
    if (!newRecipient.name || !newRecipient.phone) {
      toast.error('Nama dan nomor telepon wajib diisi');
      return;
    }
    
    try {
      await axios.post(`${API}/api/whatsapp-alerts/recipients`, newRecipient);
      toast.success('Recipient berhasil ditambahkan');
      setNewRecipient({ name: '', phone: '', role: 'admin', is_active: true, alert_types: [] });
      fetchData();
    } catch (err) {
      toast.error('Gagal menambahkan recipient');
    }
  };

  const deleteRecipient = async (id) => {
    try {
      await axios.delete(`${API}/api/whatsapp-alerts/recipients/${id}`);
      toast.success('Recipient berhasil dihapus');
      fetchData();
    } catch (err) {
      toast.error('Gagal menghapus recipient');
    }
  };

  const initTemplates = async () => {
    try {
      await axios.post(`${API}/api/whatsapp-alerts/init-templates`);
      toast.success('Templates berhasil di-initialize');
      fetchData();
    } catch (err) {
      toast.error('Gagal initialize templates');
    }
  };

  const sendTest = async () => {
    if (!testPhone) {
      toast.error('Masukkan nomor telepon');
      return;
    }
    
    try {
      const res = await axios.post(`${API}/api/whatsapp-alerts/test`, null, {
        params: { phone: testPhone, message: testMessage }
      });
      toast.success(res.data.message);
    } catch (err) {
      toast.error('Gagal mengirim test');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'bg-red-600';
      case 'high': return 'bg-orange-600';
      case 'medium': return 'bg-yellow-600';
      default: return 'bg-gray-600';
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'owner': return 'bg-purple-600';
      case 'hrd': return 'bg-blue-600';
      case 'spv': return 'bg-green-600';
      case 'gudang': return 'bg-yellow-600';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0608] to-[#1a0a0e] p-4" data-testid="whatsapp-alerts-page">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
          <MessageSquare className="h-6 w-6 text-green-400" />
          WhatsApp Alert System
        </h1>
        <p className="text-sm text-gray-400">Notifikasi otomatis via WhatsApp terintegrasi AI Command Center</p>
      </div>

      {/* Status Card */}
      <Card className={`mb-4 ${config?.is_enabled ? 'bg-green-900/20 border-green-700/30' : 'bg-red-900/20 border-red-700/30'}`}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {config?.is_enabled ? (
                <CheckCircle className="h-6 w-6 text-green-400" />
              ) : (
                <AlertTriangle className="h-6 w-6 text-yellow-400" />
              )}
              <div>
                <p className={`font-medium ${config?.is_enabled ? 'text-green-400' : 'text-yellow-400'}`}>
                  {config?.is_enabled ? 'WhatsApp Alerts Aktif' : 'WhatsApp Alerts Belum Dikonfigurasi'}
                </p>
                <p className="text-xs text-gray-400">
                  {config?.api_provider ? `Provider: ${config.api_provider}` : 'Konfigurasi API diperlukan'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Enable</span>
              <Switch 
                checked={config?.is_enabled || false}
                onCheckedChange={(checked) => setConfig({ ...config, is_enabled: checked })}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="recipients" className="space-y-4">
        <TabsList className="bg-red-950/50 p-1">
          <TabsTrigger value="recipients" className="data-[state=active]:bg-red-900/50">
            <Users className="h-4 w-4 mr-1" />
            Recipients
          </TabsTrigger>
          <TabsTrigger value="templates" className="data-[state=active]:bg-red-900/50">
            <Bell className="h-4 w-4 mr-1" />
            Alert Templates
          </TabsTrigger>
          <TabsTrigger value="config" className="data-[state=active]:bg-red-900/50">
            <Settings className="h-4 w-4 mr-1" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="logs" className="data-[state=active]:bg-red-900/50">
            <History className="h-4 w-4 mr-1" />
            Logs
          </TabsTrigger>
        </TabsList>

        {/* Recipients Tab */}
        <TabsContent value="recipients">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card className="bg-[#120a0c]/80 border-green-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100 text-sm">Tambah Recipient</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400">Nama</label>
                  <Input
                    value={newRecipient.name}
                    onChange={(e) => setNewRecipient({ ...newRecipient, name: e.target.value })}
                    placeholder="Nama recipient..."
                    className="bg-red-950/50 border-red-700/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">No. WhatsApp</label>
                  <Input
                    value={newRecipient.phone}
                    onChange={(e) => setNewRecipient({ ...newRecipient, phone: e.target.value })}
                    placeholder="628xxx..."
                    className="bg-red-950/50 border-red-700/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Role</label>
                  <Select 
                    value={newRecipient.role}
                    onValueChange={(v) => setNewRecipient({ ...newRecipient, role: v })}
                  >
                    <SelectTrigger className="bg-red-950/50 border-red-700/30">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="owner">Owner</SelectItem>
                      <SelectItem value="hrd">HRD</SelectItem>
                      <SelectItem value="spv">SPV</SelectItem>
                      <SelectItem value="gudang">Gudang</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={addRecipient} className="w-full bg-green-900/50 hover:bg-green-800/50">
                  <Plus className="h-4 w-4 mr-1" />
                  Tambah Recipient
                </Button>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2 bg-[#120a0c]/80 border-red-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100 text-sm">Daftar Recipients ({recipients.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {recipients.map((r) => (
                    <div key={r.id} className="p-3 bg-red-950/20 rounded-lg flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <User className="h-8 w-8 text-gray-500" />
                        <div>
                          <p className="font-medium text-amber-100">{r.name}</p>
                          <p className="text-xs text-gray-400">{r.phone}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={getRoleColor(r.role)}>{r.role}</Badge>
                        <Badge variant="outline" className={r.is_active ? 'text-green-400' : 'text-gray-400'}>
                          {r.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => deleteRecipient(r.id)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  {recipients.length === 0 && (
                    <p className="text-center text-gray-400 py-4">Belum ada recipient</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates">
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-amber-100">Alert Templates</CardTitle>
              <Button size="sm" onClick={initTemplates} className="bg-blue-900/50">
                <RefreshCw className="h-4 w-4 mr-1" />
                Initialize Templates
              </Button>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {templates.map((t) => (
                  <div key={t.id} className="p-3 bg-red-950/30 rounded-lg border border-red-900/30">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-medium text-amber-100">{t.template_name}</p>
                      <div className="flex gap-1">
                        <Badge className={getPriorityColor(t.priority)}>{t.priority}</Badge>
                        <Badge variant="outline" className={t.is_active ? 'text-green-400' : 'text-red-400'}>
                          {t.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    </div>
                    <div className="p-2 bg-black/30 rounded text-xs text-gray-300 font-mono whitespace-pre-wrap max-h-[100px] overflow-y-auto">
                      {t.message_template}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      Recipients: {t.default_recipients?.join(', ') || '-'}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="config">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100 text-sm">WhatsApp API Configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400">API Provider</label>
                  <Select 
                    value={config?.api_provider || ''}
                    onValueChange={(v) => setConfig({ ...config, api_provider: v })}
                  >
                    <SelectTrigger className="bg-red-950/50 border-red-700/30">
                      <SelectValue placeholder="Pilih provider..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fonnte">Fonnte</SelectItem>
                      <SelectItem value="wablas">Wablas</SelectItem>
                      <SelectItem value="woowa">WooWa</SelectItem>
                      <SelectItem value="n8n">n8n Webhook</SelectItem>
                      <SelectItem value="custom">Custom API</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs text-gray-400">API Key</label>
                  <Input
                    type="password"
                    value={config?.api_key || ''}
                    onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                    placeholder="API Key..."
                    className="bg-red-950/50 border-red-700/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">API URL</label>
                  <Input
                    value={config?.api_url || ''}
                    onChange={(e) => setConfig({ ...config, api_url: e.target.value })}
                    placeholder="https://..."
                    className="bg-red-950/50 border-red-700/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Sender Number</label>
                  <Input
                    value={config?.sender_number || ''}
                    onChange={(e) => setConfig({ ...config, sender_number: e.target.value })}
                    placeholder="628xxx..."
                    className="bg-red-950/50 border-red-700/30"
                  />
                </div>
                <Button onClick={saveConfig} className="w-full bg-green-900/50 hover:bg-green-800/50">
                  Simpan Konfigurasi
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-blue-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100 text-sm">Test Alert</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400">No. WhatsApp Tujuan</label>
                  <Input
                    value={testPhone}
                    onChange={(e) => setTestPhone(e.target.value)}
                    placeholder="628xxx..."
                    className="bg-red-950/50 border-red-700/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Pesan Test</label>
                  <Textarea
                    value={testMessage}
                    onChange={(e) => setTestMessage(e.target.value)}
                    className="bg-red-950/50 border-red-700/30"
                  />
                </div>
                <Button onClick={sendTest} className="w-full bg-blue-900/50 hover:bg-blue-800/50">
                  <Send className="h-4 w-4 mr-1" />
                  Kirim Test
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs">
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-amber-100">Alert Logs</CardTitle>
              <Button size="sm" variant="outline" onClick={fetchData}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {logs.map((log) => (
                  <div key={log.id} className="p-3 bg-red-950/20 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <Badge className={getPriorityColor(log.priority)}>{log.trigger_type}</Badge>
                        <span className="text-xs text-gray-400">{log.recipient_name}</span>
                        <span className="text-xs text-gray-500">{log.recipient_phone}</span>
                      </div>
                      <Badge variant="outline" className={log.status === 'sent' ? 'text-green-400' : 'text-yellow-400'}>
                        {log.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-300 whitespace-pre-wrap">{log.message?.slice(0, 100)}...</p>
                    <p className="text-xs text-gray-500 mt-1">{new Date(log.created_at).toLocaleString('id-ID')}</p>
                  </div>
                ))}
                {logs.length === 0 && (
                  <p className="text-center text-gray-400 py-4">Belum ada log</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WhatsAppAlerts;
