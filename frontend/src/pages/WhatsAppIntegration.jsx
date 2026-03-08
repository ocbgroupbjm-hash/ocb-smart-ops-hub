import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  MessageSquare, 
  Settings, 
  TestTube, 
  ScrollText, 
  Webhook,
  Send,
  Phone,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowUpRight,
  ArrowDownLeft,
  RefreshCw,
  Copy,
  Loader2
} from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';

export default function WhatsAppIntegration() {
  // Config state
  const [config, setConfig] = useState({
    provider_type: 'meta',
    business_phone_number: '',
    phone_number_id: '',
    business_account_id: '',
    api_token: '',
    access_token: '',
    account_sid: '',
    auth_token: '',
    default_reply_mode: 'customer_service',
    language: 'id',
    auto_reply_enabled: true,
    auto_create_crm_customer: true,
    human_handoff_enabled: false,
    fallback_when_ai_fails: 'Mohon maaf, saat ini sistem sedang sibuk. Mohon tunggu sebentar.',
    active_status: false
  });
  const [configLoading, setConfigLoading] = useState(true);
  const [configSaving, setConfigSaving] = useState(false);
  const [configExists, setConfigExists] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [activating, setActivating] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);

  // Test message state
  const [testPhone, setTestPhone] = useState('');
  const [testMessage, setTestMessage] = useState('');
  const [testProvider, setTestProvider] = useState('test');
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // Messages & logs state
  const [messages, setMessages] = useState([]);
  const [logs, setLogs] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [logsLoading, setLogsLoading] = useState(false);

  // Filters
  const [messageFilter, setMessageFilter] = useState({
    direction: '',
    phone_number: '',
    status: ''
  });

  // Webhook status
  const [webhookStatus, setWebhookStatus] = useState(null);

  useEffect(() => {
    loadConfig();
    loadMessages();
    loadLogs();
    loadWebhookStatus();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await api.get('/whatsapp/config/');
      setConfig(prev => ({
        ...prev,
        ...response.data,
        api_token: '',
        access_token: '',
        account_sid: '',
        auth_token: ''
      }));
      setConfigExists(true);
    } catch (error) {
      if (error.response?.status !== 404) {
        console.error('Load config error:', error);
      }
      setConfigExists(false);
    } finally {
      setConfigLoading(false);
    }
  };

  const loadWebhookStatus = async () => {
    try {
      const response = await api.get('/whatsapp/status/');
      setWebhookStatus(response.data);
    } catch (error) {
      console.error('Load webhook status error:', error);
    }
  };

  const loadMessages = async () => {
    setMessagesLoading(true);
    try {
      const params = {};
      if (messageFilter.direction) params.direction = messageFilter.direction;
      if (messageFilter.phone_number) params.phone_number = messageFilter.phone_number;
      if (messageFilter.status) params.status = messageFilter.status;

      const response = await api.get('/whatsapp/messages/', { params });
      setMessages(response.data);
    } catch (error) {
      console.error('Load messages error:', error);
    } finally {
      setMessagesLoading(false);
    }
  };

  const loadLogs = async () => {
    setLogsLoading(true);
    try {
      const response = await api.get('/whatsapp/logs/');
      setLogs(response.data);
    } catch (error) {
      console.error('Load logs error:', error);
    } finally {
      setLogsLoading(false);
    }
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    setConfigSaving(true);
    
    try {
      const payload = {
        provider_type: config.provider_type,
        business_phone_number: config.business_phone_number || null,
        phone_number_id: config.phone_number_id || null,
        business_account_id: config.business_account_id || null,
        default_reply_mode: config.default_reply_mode,
        language: config.language,
        auto_reply_enabled: config.auto_reply_enabled,
        auto_create_crm_customer: config.auto_create_crm_customer,
        human_handoff_enabled: config.human_handoff_enabled,
        fallback_when_ai_fails: config.fallback_when_ai_fails || null,
        active_status: config.active_status
      };

      // Add credentials based on provider
      if (config.provider_type === 'meta') {
        if (config.access_token) payload.access_token = config.access_token;
      } else if (config.provider_type === 'twilio') {
        if (config.account_sid) payload.account_sid = config.account_sid;
        if (config.auth_token) payload.auth_token = config.auth_token;
      } else {
        if (config.api_token) payload.api_token = config.api_token;
      }

      await api.post('/whatsapp/config/', payload);
      toast.success('Konfigurasi WhatsApp berhasil disimpan');
      setConfigExists(true);
      loadWebhookStatus();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Gagal menyimpan konfigurasi';
      toast.error(errorMsg);
      console.error('Save config error:', error);
    } finally {
      setConfigSaving(false);
    }
  };

  const handleTestMessage = async (e) => {
    e.preventDefault();
    setTestLoading(true);
    setTestResult(null);

    try {
      const response = await api.post('/whatsapp/test-message/', {
        phone_number: testPhone,
        message_text: testMessage,
        provider_mode: testProvider
      });
      setTestResult(response.data);
      toast.success('Test message berhasil diproses');
      loadMessages();
      loadLogs();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Gagal mengirim test message';
      toast.error(errorMsg);
      setTestResult({ success: false, error: errorMsg });
    } finally {
      setTestLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setConnectionStatus(null);
    
    try {
      const response = await api.post('/whatsapp/test-connection/');
      setConnectionStatus(response.data);
      if (response.data.success) {
        toast.success('Koneksi berhasil! Provider terhubung dengan baik.');
      } else {
        toast.error(response.data.error || 'Koneksi gagal. Periksa kredensial Anda.');
      }
    } catch (error) {
      const errorDetail = error.response?.data?.detail;
      let errorMsg = 'Gagal menguji koneksi';
      
      if (typeof errorDetail === 'string') {
        if (errorDetail.includes('credentials')) {
          errorMsg = 'Kredensial tidak valid atau belum dikonfigurasi';
        } else if (errorDetail.includes('provider')) {
          errorMsg = 'Provider belum dikonfigurasi dengan benar';
        } else if (errorDetail.includes('token')) {
          errorMsg = 'Access token tidak valid atau sudah kadaluarsa';
        } else {
          errorMsg = errorDetail;
        }
      }
      
      toast.error(errorMsg);
      setConnectionStatus({ success: false, error: errorMsg });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleToggleActivation = async () => {
    setActivating(true);
    
    try {
      const newStatus = !config.active_status;
      await api.post('/whatsapp/config/', {
        ...config,
        active_status: newStatus
      });
      
      setConfig(prev => ({ ...prev, active_status: newStatus }));
      loadWebhookStatus();
      
      if (newStatus) {
        toast.success('Integrasi WhatsApp berhasil diaktifkan!');
      } else {
        toast.success('Integrasi WhatsApp dinonaktifkan.');
      }
    } catch (error) {
      const errorDetail = error.response?.data?.detail;
      let errorMsg = 'Gagal mengubah status integrasi';
      
      if (typeof errorDetail === 'string') {
        if (errorDetail.includes('credentials')) {
          errorMsg = 'Tidak dapat mengaktifkan: Kredensial provider belum lengkap';
        } else if (errorDetail.includes('phone')) {
          errorMsg = 'Tidak dapat mengaktifkan: Nomor telepon bisnis belum dikonfigurasi';
        } else {
          errorMsg = errorDetail;
        }
      }
      
      toast.error(errorMsg);
    } finally {
      setActivating(false);
    }
  };

  const getProviderFields = () => {
    switch (config.provider_type) {
      case 'meta':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="phone_number_id">Phone Number ID</Label>
              <Input
                id="phone_number_id"
                value={config.phone_number_id}
                onChange={(e) => setConfig({ ...config, phone_number_id: e.target.value })}
                placeholder="Meta WhatsApp Phone Number ID"
                data-testid="phone-number-id-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="business_account_id">Business Account ID</Label>
              <Input
                id="business_account_id"
                value={config.business_account_id}
                onChange={(e) => setConfig({ ...config, business_account_id: e.target.value })}
                placeholder="Meta WhatsApp Business Account ID"
                data-testid="business-account-id-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="access_token">Access Token</Label>
              <Input
                id="access_token"
                type="password"
                value={config.access_token}
                onChange={(e) => setConfig({ ...config, access_token: e.target.value })}
                placeholder="Meta WhatsApp Access Token"
                data-testid="access-token-input"
              />
              {configExists && (
                <p className="text-xs text-muted-foreground">Token tersimpan (masked). Isi ulang untuk mengubah.</p>
              )}
            </div>
          </>
        );
      case 'twilio':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="account_sid">Account SID</Label>
              <Input
                id="account_sid"
                value={config.account_sid}
                onChange={(e) => setConfig({ ...config, account_sid: e.target.value })}
                placeholder="Twilio Account SID"
                data-testid="account-sid-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="auth_token">Auth Token</Label>
              <Input
                id="auth_token"
                type="password"
                value={config.auth_token}
                onChange={(e) => setConfig({ ...config, auth_token: e.target.value })}
                placeholder="Twilio Auth Token"
                data-testid="auth-token-input"
              />
              {configExists && (
                <p className="text-xs text-muted-foreground">Token tersimpan (masked). Isi ulang untuk mengubah.</p>
              )}
            </div>
          </>
        );
      default:
        return (
          <div className="space-y-2">
            <Label htmlFor="api_token">API Token</Label>
            <Input
              id="api_token"
              type="password"
              value={config.api_token}
              onChange={(e) => setConfig({ ...config, api_token: e.target.value })}
              placeholder="API Token"
              data-testid="api-token-input"
            />
            {configExists && (
              <p className="text-xs text-muted-foreground">Token tersimpan (masked). Isi ulang untuk mengubah.</p>
            )}
          </div>
        );
    }
  };

  return (
    <div className="space-y-6" data-testid="whatsapp-integration-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
            WhatsApp Integration
          </h1>
          <p className="text-gray-500">Kelola integrasi WhatsApp Business untuk AI customer service</p>
        </div>
        <div className="flex items-center gap-2">
          {webhookStatus?.active ? (
            <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Active
            </Badge>
          ) : (
            <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
              <AlertCircle className="h-3 w-3 mr-1" />
              Inactive
            </Badge>
          )}
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="config" className="space-y-6">
        <TabsList className="bg-card/50 border border-border/50">
          <TabsTrigger value="config" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
            <Settings className="h-4 w-4 mr-2" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="test" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
            <TestTube className="h-4 w-4 mr-2" />
            Test Simulator
          </TabsTrigger>
          <TabsTrigger value="messages" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
            <MessageSquare className="h-4 w-4 mr-2" />
            Messages
          </TabsTrigger>
          <TabsTrigger value="logs" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
            <ScrollText className="h-4 w-4 mr-2" />
            Logs
          </TabsTrigger>
          <TabsTrigger value="webhook" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
            <Webhook className="h-4 w-4 mr-2" />
            Webhook
          </TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-6">
          {configLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : (
            <form onSubmit={handleSaveConfig}>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Provider Settings */}
                <Card className="bg-card/50 backdrop-blur-sm border-border/50">
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Phone className="h-5 w-5 text-primary" />
                      Provider Settings
                    </CardTitle>
                    <CardDescription>Configure your WhatsApp provider credentials</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="provider_type">Provider</Label>
                      <Select 
                        value={config.provider_type} 
                        onValueChange={(value) => setConfig({ ...config, provider_type: value })}
                      >
                        <SelectTrigger data-testid="provider-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="meta">Meta WhatsApp Business</SelectItem>
                          <SelectItem value="twilio">Twilio</SelectItem>
                          <SelectItem value="360dialog">360dialog</SelectItem>
                          <SelectItem value="custom">Custom Webhook</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="business_phone_number">Business Phone Number</Label>
                      <Input
                        id="business_phone_number"
                        value={config.business_phone_number}
                        onChange={(e) => setConfig({ ...config, business_phone_number: e.target.value })}
                        placeholder="+62812345678"
                        data-testid="business-phone-input"
                      />
                    </div>

                    {getProviderFields()}
                  </CardContent>
                </Card>

                {/* AI Settings */}
                <Card className="bg-card/50 backdrop-blur-sm border-border/50">
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <MessageSquare className="h-5 w-5 text-primary" />
                      AI Reply Settings
                    </CardTitle>
                    <CardDescription>Configure AI auto-reply behavior</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="default_reply_mode">Reply Mode</Label>
                      <Select 
                        value={config.default_reply_mode} 
                        onValueChange={(value) => setConfig({ ...config, default_reply_mode: value })}
                      >
                        <SelectTrigger data-testid="reply-mode-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="customer_service">Customer Service</SelectItem>
                          <SelectItem value="sales">Sales</SelectItem>
                          <SelectItem value="marketing">Marketing</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="language">Language</Label>
                      <Select 
                        value={config.language} 
                        onValueChange={(value) => setConfig({ ...config, language: value })}
                      >
                        <SelectTrigger data-testid="language-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="id">Bahasa Indonesia</SelectItem>
                          <SelectItem value="en">English</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="fallback_message">Fallback Message</Label>
                      <Textarea
                        id="fallback_message"
                        value={config.fallback_when_ai_fails}
                        onChange={(e) => setConfig({ ...config, fallback_when_ai_fails: e.target.value })}
                        placeholder="Pesan fallback ketika AI gagal..."
                        rows={3}
                        data-testid="fallback-message-input"
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Toggle Settings */}
                <Card className="bg-card/50 backdrop-blur-sm border-border/50 lg:col-span-2">
                  <CardHeader>
                    <CardTitle className="text-lg">Automation Settings</CardTitle>
                    <CardDescription>Enable or disable automation features</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                      <div className="flex items-center justify-between space-x-2 p-4 rounded-lg bg-white/5 border border-border/30">
                        <div>
                          <Label htmlFor="auto_reply">Auto Reply</Label>
                          <p className="text-xs text-muted-foreground">AI akan otomatis membalas pesan</p>
                        </div>
                        <Switch
                          id="auto_reply"
                          checked={config.auto_reply_enabled}
                          onCheckedChange={(checked) => setConfig({ ...config, auto_reply_enabled: checked })}
                          data-testid="auto-reply-switch"
                        />
                      </div>

                      <div className="flex items-center justify-between space-x-2 p-4 rounded-lg bg-white/5 border border-border/30">
                        <div>
                          <Label htmlFor="auto_crm">Auto CRM</Label>
                          <p className="text-xs text-muted-foreground">Buat customer otomatis di CRM</p>
                        </div>
                        <Switch
                          id="auto_crm"
                          checked={config.auto_create_crm_customer}
                          onCheckedChange={(checked) => setConfig({ ...config, auto_create_crm_customer: checked })}
                          data-testid="auto-crm-switch"
                        />
                      </div>

                      <div className="flex items-center justify-between space-x-2 p-4 rounded-lg bg-white/5 border border-border/30">
                        <div>
                          <Label htmlFor="human_handoff">Human Handoff</Label>
                          <p className="text-xs text-muted-foreground">Eskalasi ke manusia jika perlu</p>
                        </div>
                        <Switch
                          id="human_handoff"
                          checked={config.human_handoff_enabled}
                          onCheckedChange={(checked) => setConfig({ ...config, human_handoff_enabled: checked })}
                          data-testid="human-handoff-switch"
                        />
                      </div>

                      <div className="flex items-center justify-between space-x-2 p-4 rounded-lg bg-white/5 border border-border/30">
                        <div>
                          <Label htmlFor="active_status">Active Status</Label>
                          <p className="text-xs text-muted-foreground">Aktifkan integrasi WhatsApp</p>
                        </div>
                        <Switch
                          id="active_status"
                          checked={config.active_status}
                          onCheckedChange={(checked) => setConfig({ ...config, active_status: checked })}
                          data-testid="active-status-switch"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="flex justify-end gap-4 mt-6">
                <Button 
                  type="button"
                  variant="outline"
                  onClick={handleTestConnection}
                  disabled={testingConnection || !configExists}
                  data-testid="test-connection-button"
                  className="border-red-900/30 text-red-200 hover:bg-red-900/20"
                >
                  {testingConnection ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    <>
                      <Webhook className="h-4 w-4 mr-2" />
                      Test Connection
                    </>
                  )}
                </Button>
                <Button 
                  type="button"
                  variant={config.active_status ? "destructive" : "default"}
                  onClick={handleToggleActivation}
                  disabled={activating || !configExists}
                  data-testid="activate-integration-button"
                  className={config.active_status 
                    ? "bg-red-600 hover:bg-red-700" 
                    : "bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400"
                  }
                >
                  {activating ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : config.active_status ? (
                    <>
                      <XCircle className="h-4 w-4 mr-2" />
                      Deactivate Integration
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      Activate Integration
                    </>
                  )}
                </Button>
                <Button 
                  type="submit" 
                  disabled={configSaving}
                  data-testid="save-config-button"
                  className="bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500 shadow-lg shadow-red-900/30"
                >
                  {configSaving ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Menyimpan...
                    </>
                  ) : (
                    'Save Configuration'
                  )}
                </Button>
              </div>
            </form>
          )}
        </TabsContent>

        {/* Test Simulator Tab */}
        <TabsContent value="test" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-card/50 backdrop-blur-sm border-border/50">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <TestTube className="h-5 w-5 text-primary" />
                  Test Message Simulator
                </CardTitle>
                <CardDescription>Simulasikan pesan masuk untuk menguji AI response</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleTestMessage} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="test_phone">Phone Number</Label>
                    <Input
                      id="test_phone"
                      value={testPhone}
                      onChange={(e) => setTestPhone(e.target.value)}
                      placeholder="+6281234567890"
                      required
                      data-testid="test-phone-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="test_message">Message</Label>
                    <Textarea
                      id="test_message"
                      value={testMessage}
                      onChange={(e) => setTestMessage(e.target.value)}
                      placeholder="Halo, saya mau tanya tentang produk..."
                      rows={4}
                      required
                      data-testid="test-message-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="test_provider">Provider Mode</Label>
                    <Select value={testProvider} onValueChange={setTestProvider}>
                      <SelectTrigger data-testid="test-provider-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="test">Test Mode</SelectItem>
                        <SelectItem value="meta">Meta WhatsApp</SelectItem>
                        <SelectItem value="twilio">Twilio</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full" 
                    disabled={testLoading || !configExists}
                    data-testid="send-test-button"
                  >
                    {testLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4 mr-2" />
                        Simulate Incoming Message
                      </>
                    )}
                  </Button>

                  {!configExists && (
                    <p className="text-xs text-yellow-400 text-center">
                      Simpan konfigurasi terlebih dahulu sebelum melakukan test
                    </p>
                  )}
                </form>
              </CardContent>
            </Card>

            {/* Test Result */}
            <Card className="bg-card/50 backdrop-blur-sm border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">Test Result</CardTitle>
                <CardDescription>Hasil simulasi pesan WhatsApp</CardDescription>
              </CardHeader>
              <CardContent>
                {testResult ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      {testResult.success ? (
                        <Badge className="bg-green-500/20 text-green-400">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Success
                        </Badge>
                      ) : (
                        <Badge className="bg-red-500/20 text-red-400">
                          <XCircle className="h-3 w-3 mr-1" />
                          Failed
                        </Badge>
                      )}
                      {testResult.test_mode && (
                        <Badge variant="outline">Test Mode</Badge>
                      )}
                    </div>

                    {testResult.result && (
                      <div className="space-y-3">
                        {testResult.result.crm_auto_created && (
                          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
                            <p className="text-sm text-blue-400">
                              <CheckCircle2 className="h-4 w-4 inline mr-1" />
                              Customer baru dibuat di CRM
                            </p>
                          </div>
                        )}

                        <div className="p-3 rounded-lg bg-white/5 border border-border/30">
                          <Label className="text-xs text-muted-foreground">Conversation ID</Label>
                          <p className="text-sm font-mono">{testResult.result.conversation_id}</p>
                        </div>

                        {testResult.result.ai_response && (
                          <div className="p-3 rounded-lg bg-primary/10 border border-primary/30">
                            <Label className="text-xs text-muted-foreground mb-2 block">AI Response</Label>
                            <p className="text-sm whitespace-pre-wrap">{testResult.result.ai_response}</p>
                          </div>
                        )}

                        {testResult.result.needs_human_handoff && (
                          <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                            <p className="text-sm text-yellow-400">
                              <AlertCircle className="h-4 w-4 inline mr-1" />
                              Memerlukan handoff ke manusia
                            </p>
                            {testResult.result.handoff_reason && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Alasan: {testResult.result.handoff_reason}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {testResult.error && (
                      <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                        <p className="text-sm text-red-400">{testResult.error}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                    <TestTube className="h-12 w-12 mb-4 opacity-50" />
                    <p>Belum ada hasil test</p>
                    <p className="text-xs">Kirim test message untuk melihat hasil</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Messages Tab */}
        <TabsContent value="messages" className="space-y-6">
          <Card className="bg-card/50 backdrop-blur-sm border-border/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <MessageSquare className="h-5 w-5 text-primary" />
                    WhatsApp Messages
                  </CardTitle>
                  <CardDescription>Riwayat semua pesan WhatsApp</CardDescription>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={loadMessages}
                  disabled={messagesLoading}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${messagesLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              <div className="flex flex-wrap gap-4 mb-6">
                <div className="w-40">
                  <Select 
                    value={messageFilter.direction || "all"} 
                    onValueChange={(v) => setMessageFilter({ ...messageFilter, direction: v === "all" ? "" : v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Direction" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="incoming">Incoming</SelectItem>
                      <SelectItem value="outgoing">Outgoing</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Input
                  placeholder="Phone number..."
                  value={messageFilter.phone_number}
                  onChange={(e) => setMessageFilter({ ...messageFilter, phone_number: e.target.value })}
                  className="w-48"
                />
                <div className="w-40">
                  <Select 
                    value={messageFilter.status || "all"} 
                    onValueChange={(v) => setMessageFilter({ ...messageFilter, status: v === "all" ? "" : v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="sent">Sent</SelectItem>
                      <SelectItem value="delivered">Delivered</SelectItem>
                      <SelectItem value="read">Read</SelectItem>
                      <SelectItem value="failed">Failed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={loadMessages} variant="secondary" size="sm">
                  Apply Filters
                </Button>
              </div>

              {/* Messages Table */}
              {messagesLoading ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <MessageSquare className="h-12 w-12 mb-4 opacity-50" />
                  <p>Belum ada pesan WhatsApp</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border/50">
                        <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">TIME</th>
                        <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">DIRECTION</th>
                        <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">PHONE</th>
                        <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">MESSAGE</th>
                        <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">STATUS</th>
                        <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">AI MODE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {messages.map((msg) => (
                        <tr key={msg.id} className="border-b border-border/30 hover:bg-white/5">
                          <td className="py-3 px-4 text-sm text-muted-foreground">
                            {new Date(msg.timestamp).toLocaleString('id-ID')}
                          </td>
                          <td className="py-3 px-4">
                            {msg.direction === 'incoming' ? (
                              <Badge variant="outline" className="text-blue-400 border-blue-400/30">
                                <ArrowDownLeft className="h-3 w-3 mr-1" />
                                Incoming
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-green-400 border-green-400/30">
                                <ArrowUpRight className="h-3 w-3 mr-1" />
                                Outgoing
                              </Badge>
                            )}
                          </td>
                          <td className="py-3 px-4 text-sm font-mono">{msg.phone_number}</td>
                          <td className="py-3 px-4 text-sm max-w-xs truncate">{msg.message_text}</td>
                          <td className="py-3 px-4">
                            <Badge 
                              className={
                                msg.delivery_status === 'delivered' || msg.delivery_status === 'read' 
                                  ? 'bg-green-500/20 text-green-400' 
                                  : msg.delivery_status === 'failed'
                                    ? 'bg-red-500/20 text-red-400'
                                    : 'bg-yellow-500/20 text-yellow-400'
                              }
                            >
                              {msg.delivery_status}
                            </Badge>
                          </td>
                          <td className="py-3 px-4 text-sm text-muted-foreground">
                            {msg.ai_mode_used || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-6">
          <Card className="bg-card/50 backdrop-blur-sm border-border/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <ScrollText className="h-5 w-5 text-primary" />
                    System Logs
                  </CardTitle>
                  <CardDescription>Log aktivitas sistem WhatsApp integration</CardDescription>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={loadLogs}
                  disabled={logsLoading}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${logsLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {logsLoading ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : logs.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <ScrollText className="h-12 w-12 mb-4 opacity-50" />
                  <p>Belum ada log aktivitas</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {logs.map((log) => (
                    <div 
                      key={log.id} 
                      className={`p-3 rounded-lg border ${
                        log.success 
                          ? 'bg-white/5 border-border/30' 
                          : 'bg-red-500/10 border-red-500/30'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <Badge 
                            variant="outline" 
                            className={
                              log.log_type === 'error' 
                                ? 'text-red-400 border-red-400/30' 
                                : log.log_type === 'ai'
                                  ? 'text-purple-400 border-purple-400/30'
                                  : log.log_type === 'crm'
                                    ? 'text-blue-400 border-blue-400/30'
                                    : 'text-gray-400 border-gray-400/30'
                            }
                          >
                            {log.log_type}
                          </Badge>
                          {log.phone_number && (
                            <span className="text-xs text-muted-foreground font-mono">
                              {log.phone_number}
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(log.timestamp).toLocaleString('id-ID')}
                        </span>
                      </div>
                      <p className="text-sm mt-2">{log.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Webhook Tab */}
        <TabsContent value="webhook" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-card/50 backdrop-blur-sm border-border/50">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Webhook className="h-5 w-5 text-primary" />
                  Webhook Configuration
                </CardTitle>
                <CardDescription>URL webhook untuk menerima pesan dari provider</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Webhook URL</Label>
                  <div className="flex gap-2">
                    <Input 
                      value={`${process.env.REACT_APP_BACKEND_URL}/api/whatsapp/webhook/`}
                      readOnly
                      className="font-mono text-sm"
                    />
                    <Button 
                      variant="outline" 
                      size="icon"
                      onClick={() => copyToClipboard(`${process.env.REACT_APP_BACKEND_URL}/api/whatsapp/webhook/`)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {config.verify_token && (
                  <div className="space-y-2">
                    <Label>Verify Token</Label>
                    <div className="flex gap-2">
                      <Input 
                        value={config.verify_token}
                        readOnly
                        className="font-mono text-sm"
                      />
                      <Button 
                        variant="outline" 
                        size="icon"
                        onClick={() => copyToClipboard(config.verify_token)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="bg-card/50 backdrop-blur-sm border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">Integration Status</CardTitle>
                <CardDescription>Status koneksi WhatsApp integration</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {webhookStatus ? (
                  <>
                    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-border/30">
                      <span className="text-sm">Configuration</span>
                      {webhookStatus.configured ? (
                        <Badge className="bg-green-500/20 text-green-400">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Configured
                        </Badge>
                      ) : (
                        <Badge className="bg-yellow-500/20 text-yellow-400">
                          <AlertCircle className="h-3 w-3 mr-1" />
                          Not Configured
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-border/30">
                      <span className="text-sm">Active Status</span>
                      {webhookStatus.active ? (
                        <Badge className="bg-green-500/20 text-green-400">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Active
                        </Badge>
                      ) : (
                        <Badge className="bg-gray-500/20 text-gray-400">
                          <XCircle className="h-3 w-3 mr-1" />
                          Inactive
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-border/30">
                      <span className="text-sm">Provider</span>
                      <Badge variant="outline">{webhookStatus.provider || 'Not Set'}</Badge>
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-border/30">
                      <span className="text-sm">Credentials</span>
                      {webhookStatus.has_credentials ? (
                        <Badge className="bg-green-500/20 text-green-400">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Set
                        </Badge>
                      ) : (
                        <Badge className="bg-yellow-500/20 text-yellow-400">
                          <AlertCircle className="h-3 w-3 mr-1" />
                          Required
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-border/30">
                      <span className="text-sm">Auto Reply</span>
                      {webhookStatus.auto_reply_enabled ? (
                        <Badge className="bg-blue-500/20 text-blue-400">Enabled</Badge>
                      ) : (
                        <Badge className="bg-gray-500/20 text-gray-400">Disabled</Badge>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
