import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  MessageSquare, 
  Send,
  Phone,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowUpRight,
  ArrowDownLeft,
  RefreshCw,
  Wifi,
  WifiOff,
  Users,
  ScrollText,
  Zap,
  Bot,
  User,
  Loader2,
  Search
} from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';

export default function WAHAMonitor() {
  // Connection status
  const [wahaStatus, setWahaStatus] = useState(null);
  const [wahaConfig, setWahaConfig] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);

  // Messages & Conversations
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [logs, setLogs] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);

  // Selected conversation
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [conversationMessages, setConversationMessages] = useState([]);

  // Manual send
  const [sendPhone, setSendPhone] = useState('');
  const [sendText, setSendText] = useState('');
  const [sending, setSending] = useState(false);

  // Test
  const [testPhone, setTestPhone] = useState('');
  const [testMessage, setTestMessage] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // Config update
  const [newBaseUrl, setNewBaseUrl] = useState('');
  const [newApiKey, setNewApiKey] = useState('');
  const [updatingConfig, setUpdatingConfig] = useState(false);

  // Filters
  const [phoneFilter, setPhoneFilter] = useState('');

  // Auto-refresh
  const [autoRefresh, setAutoRefresh] = useState(true);
  const refreshInterval = useRef(null);

  useEffect(() => {
    loadAll();
    
    if (autoRefresh) {
      refreshInterval.current = setInterval(loadAll, 10000);
    }
    
    return () => {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current);
      }
    };
  }, [autoRefresh]);

  const loadAll = async () => {
    await Promise.all([
      loadStatus(),
      loadConfig(),
      loadMessages(),
      loadConversations(),
      loadLogs(),
      loadCustomers()
    ]);
  };

  const loadStatus = async () => {
    try {
      const response = await api.get('/whatsapp/waha/status/');
      setWahaStatus(response.data);
    } catch (error) {
      console.error('WAHA status error:', error);
      setWahaStatus({ connected: false, error: 'Failed to check status' });
    } finally {
      setStatusLoading(false);
    }
  };

  const loadConfig = async () => {
    try {
      const response = await api.get('/whatsapp/waha/config/');
      setWahaConfig(response.data);
    } catch (error) {
      console.error('WAHA config error:', error);
    }
  };

  const handleUpdateConfig = async (e) => {
    e.preventDefault();
    setUpdatingConfig(true);
    
    try {
      const payload = {};
      if (newBaseUrl) payload.base_url = newBaseUrl;
      if (newApiKey) payload.api_key = newApiKey;
      
      const response = await api.post('/whatsapp/waha/config/', payload);
      
      if (response.data.connection_test?.connected) {
        toast.success('WAHA server connected successfully!');
      } else {
        toast.warning('Configuration saved. Connection test: ' + (response.data.connection_test?.error || 'pending'));
      }
      
      setNewBaseUrl('');
      setNewApiKey('');
      loadConfig();
      loadStatus();
    } catch (error) {
      toast.error('Failed to update config: ' + error.message);
    } finally {
      setUpdatingConfig(false);
    }
  };

  const loadMessages = async () => {
    try {
      const params = {};
      if (phoneFilter) params.phone = phoneFilter;
      const response = await api.get('/whatsapp/waha/messages/', { params });
      setMessages(response.data);
    } catch (error) {
      console.error('Load messages error:', error);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await api.get('/whatsapp/waha/conversations/');
      setConversations(response.data);
    } catch (error) {
      console.error('Load conversations error:', error);
    }
  };

  const loadLogs = async () => {
    try {
      const response = await api.get('/whatsapp/waha/logs/');
      setLogs(response.data);
    } catch (error) {
      console.error('Load logs error:', error);
    }
  };

  const loadCustomers = async () => {
    try {
      const response = await api.get('/whatsapp/waha/customers/');
      setCustomers(response.data);
    } catch (error) {
      console.error('Load customers error:', error);
    }
  };

  const loadConversationMessages = async (conversationId) => {
    try {
      const response = await api.get(`/whatsapp/waha/conversations/${conversationId}/messages/`);
      setConversationMessages(response.data);
    } catch (error) {
      console.error('Load conversation messages error:', error);
    }
  };

  const handleSelectConversation = async (conv) => {
    setSelectedConversation(conv);
    await loadConversationMessages(conv.id);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    setSending(true);
    
    try {
      const response = await api.post('/whatsapp/waha/send/', {
        phone: sendPhone,
        text: sendText
      });
      
      if (response.data.success) {
        toast.success('Pesan berhasil dikirim via WAHA');
        setSendText('');
        loadMessages();
        loadLogs();
      } else {
        toast.error(response.data.error || 'Gagal mengirim pesan');
      }
    } catch (error) {
      toast.error('Error: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSending(false);
    }
  };

  const handleTestFlow = async (e) => {
    e.preventDefault();
    setTesting(true);
    setTestResult(null);
    
    try {
      const response = await api.post('/whatsapp/waha/test/', {
        phone: testPhone,
        message: testMessage
      });
      
      setTestResult(response.data);
      
      if (response.data.success) {
        toast.success('Test flow berhasil - Pesan terkirim via WAHA');
        loadMessages();
        loadConversations();
        loadLogs();
        loadCustomers();
      } else {
        toast.error(response.data.error || 'Test flow gagal');
      }
    } catch (error) {
      toast.error('Error: ' + (error.response?.data?.detail || error.message));
      setTestResult({ success: false, error: error.message });
    } finally {
      setTesting(false);
    }
  };

  const getLogTypeColor = (type) => {
    switch (type) {
      case 'waha_incoming': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'waha_sent': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'ai_response': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'crm_auto_create': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'waha_error':
      case 'ai_error': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className="space-y-6" data-testid="waha-monitor-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2 bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent">
            WAHA WhatsApp Monitor
          </h1>
          <p className="text-red-300/60">Real-time WhatsApp AI automation monitoring</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Connection Status */}
          {statusLoading ? (
            <Badge className="bg-gray-500/20 text-gray-400">
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              Checking...
            </Badge>
          ) : wahaStatus?.connected ? (
            <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
              <Wifi className="h-3 w-3 mr-1" />
              WAHA Connected
            </Badge>
          ) : (
            <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
              <WifiOff className="h-3 w-3 mr-1" />
              WAHA Disconnected
            </Badge>
          )}
          
          <Button 
            variant="outline" 
            size="sm" 
            onClick={loadAll}
            className="border-red-900/30 text-red-200 hover:bg-red-900/20"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-300/60">Total Messages</p>
                <p className="text-3xl font-bold text-amber-100">{messages.length}</p>
              </div>
              <MessageSquare className="h-8 w-8 text-red-400/50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-300/60">Conversations</p>
                <p className="text-3xl font-bold text-amber-100">{conversations.length}</p>
              </div>
              <Users className="h-8 w-8 text-red-400/50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-300/60">WhatsApp Customers</p>
                <p className="text-3xl font-bold text-amber-100">{customers.length}</p>
              </div>
              <Phone className="h-8 w-8 text-red-400/50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-300/60">System Logs</p>
                <p className="text-3xl font-bold text-amber-100">{logs.length}</p>
              </div>
              <ScrollText className="h-8 w-8 text-red-400/50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="live" className="space-y-6">
        <TabsList className="bg-card/50 border border-border/50">
          <TabsTrigger value="live" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
            <Zap className="h-4 w-4 mr-2" />
            Live Feed
          </TabsTrigger>
          <TabsTrigger value="conversations" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
            <MessageSquare className="h-4 w-4 mr-2" />
            Conversations
          </TabsTrigger>
          <TabsTrigger value="send" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
            <Send className="h-4 w-4 mr-2" />
            Send Message
          </TabsTrigger>
          <TabsTrigger value="test" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
            <Bot className="h-4 w-4 mr-2" />
            Test Flow
          </TabsTrigger>
          <TabsTrigger value="logs" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
            <ScrollText className="h-4 w-4 mr-2" />
            System Logs
          </TabsTrigger>
          <TabsTrigger value="config" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
            <Wifi className="h-4 w-4 mr-2" />
            WAHA Config
          </TabsTrigger>
        </TabsList>

        {/* Live Feed Tab */}
        <TabsContent value="live" className="space-y-4">
          <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-amber-100 flex items-center gap-2">
                    <Zap className="h-5 w-5 text-amber-400" />
                    Live Message Feed
                  </CardTitle>
                  <CardDescription className="text-red-300/60">Real-time WhatsApp messages via WAHA</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="Filter by phone..."
                    value={phoneFilter}
                    onChange={(e) => setPhoneFilter(e.target.value)}
                    className="w-48 bg-red-950/30 border-red-900/30 text-amber-50"
                  />
                  <Button onClick={loadMessages} variant="outline" size="sm" className="border-red-900/30">
                    <Search className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {messages.length === 0 ? (
                  <div className="text-center py-12 text-red-300/60">
                    <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Belum ada pesan WhatsApp</p>
                    <p className="text-xs">Pesan akan muncul secara real-time</p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div 
                      key={msg.id} 
                      className={`p-4 rounded-lg border ${
                        msg.direction === 'incoming' 
                          ? 'bg-blue-500/10 border-blue-500/30' 
                          : 'bg-green-500/10 border-green-500/30'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {msg.direction === 'incoming' ? (
                            <Badge className="bg-blue-500/20 text-blue-400">
                              <ArrowDownLeft className="h-3 w-3 mr-1" />
                              Incoming
                            </Badge>
                          ) : (
                            <Badge className="bg-green-500/20 text-green-400">
                              <ArrowUpRight className="h-3 w-3 mr-1" />
                              Outgoing
                            </Badge>
                          )}
                          <span className="text-sm font-mono text-amber-200">{msg.phone_number}</span>
                        </div>
                        <span className="text-xs text-red-300/50">
                          {new Date(msg.timestamp).toLocaleString('id-ID')}
                        </span>
                      </div>
                      <p className="text-sm text-red-100">{msg.message_text}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge 
                          variant="outline" 
                          className={
                            msg.delivery_status === 'sent' || msg.delivery_status === 'received'
                              ? 'text-green-400 border-green-400/30'
                              : msg.delivery_status === 'failed'
                                ? 'text-red-400 border-red-400/30'
                                : 'text-yellow-400 border-yellow-400/30'
                          }
                        >
                          {msg.delivery_status}
                        </Badge>
                        {msg.ai_mode && (
                          <Badge variant="outline" className="text-purple-400 border-purple-400/30">
                            AI: {msg.ai_mode}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Conversations Tab */}
        <TabsContent value="conversations" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Conversation List */}
            <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100">Conversations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {conversations.length === 0 ? (
                    <p className="text-center py-8 text-red-300/60">No conversations yet</p>
                  ) : (
                    conversations.map((conv) => (
                      <button
                        key={conv.id}
                        onClick={() => handleSelectConversation(conv)}
                        className={`w-full text-left p-3 rounded-lg border transition-all ${
                          selectedConversation?.id === conv.id
                            ? 'bg-red-900/30 border-amber-500/50'
                            : 'bg-red-950/30 border-red-900/30 hover:border-red-700/50'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <User className="h-4 w-4 text-amber-400" />
                          <span className="font-medium text-amber-100 text-sm">{conv.customer_name}</span>
                        </div>
                        <p className="text-xs text-red-300/60 font-mono">{conv.customer_phone}</p>
                      </button>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Conversation Messages */}
            <Card className="lg:col-span-2 bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100">
                  {selectedConversation 
                    ? `Chat with ${selectedConversation.customer_name}`
                    : 'Select a conversation'
                  }
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[400px] overflow-y-auto">
                  {!selectedConversation ? (
                    <p className="text-center py-12 text-red-300/60">
                      Select a conversation to view messages
                    </p>
                  ) : conversationMessages.length === 0 ? (
                    <p className="text-center py-12 text-red-300/60">No messages</p>
                  ) : (
                    conversationMessages.map((msg) => (
                      <div 
                        key={msg.id}
                        className={`flex ${msg.role === 'user' ? 'justify-start' : 'justify-end'}`}
                      >
                        <div className={`max-w-[80%] p-3 rounded-lg ${
                          msg.role === 'user'
                            ? 'bg-blue-500/20 border border-blue-500/30'
                            : 'bg-green-500/20 border border-green-500/30'
                        }`}>
                          <div className="flex items-center gap-2 mb-1">
                            {msg.role === 'user' ? (
                              <User className="h-3 w-3 text-blue-400" />
                            ) : (
                              <Bot className="h-3 w-3 text-green-400" />
                            )}
                            <span className="text-xs text-red-300/50">
                              {msg.role === 'user' ? 'Customer' : 'AI'}
                            </span>
                          </div>
                          <p className="text-sm text-red-100">{msg.content}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Send Message Tab */}
        <TabsContent value="send" className="space-y-4">
          <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Send className="h-5 w-5 text-amber-400" />
                Manual Send Message
              </CardTitle>
              <CardDescription className="text-red-300/60">
                Kirim pesan WhatsApp langsung via WAHA
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSendMessage} className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-red-200/80">Phone Number</Label>
                  <Input
                    value={sendPhone}
                    onChange={(e) => setSendPhone(e.target.value)}
                    placeholder="+6281234567890"
                    required
                    className="bg-red-950/30 border-red-900/30 text-amber-50"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-red-200/80">Message</Label>
                  <Textarea
                    value={sendText}
                    onChange={(e) => setSendText(e.target.value)}
                    placeholder="Tulis pesan..."
                    rows={4}
                    required
                    className="bg-red-950/30 border-red-900/30 text-amber-50"
                  />
                </div>
                <Button 
                  type="submit" 
                  disabled={sending}
                  className="bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500"
                >
                  {sending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Send via WAHA
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Test Flow Tab */}
        <TabsContent value="test" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100 flex items-center gap-2">
                  <Bot className="h-5 w-5 text-amber-400" />
                  Test Complete Flow
                </CardTitle>
                <CardDescription className="text-red-300/60">
                  Simulasi pesan masuk → AI Response → WAHA Send
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleTestFlow} className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-red-200/80">Phone Number</Label>
                    <Input
                      value={testPhone}
                      onChange={(e) => setTestPhone(e.target.value)}
                      placeholder="+6281234567890"
                      required
                      className="bg-red-950/30 border-red-900/30 text-amber-50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-red-200/80">Simulated Customer Message</Label>
                    <Textarea
                      value={testMessage}
                      onChange={(e) => setTestMessage(e.target.value)}
                      placeholder="Ada powerbank yang bagus?"
                      rows={3}
                      required
                      className="bg-red-950/30 border-red-900/30 text-amber-50"
                    />
                  </div>
                  <Button 
                    type="submit" 
                    disabled={testing}
                    className="w-full bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400"
                  >
                    {testing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4 mr-2" />
                        Test Full Flow (Real Send)
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100">Test Result</CardTitle>
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
                    </div>

                    {testResult.result && (
                      <div className="space-y-3">
                        {testResult.result.crm_auto_created && (
                          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                            <p className="text-sm text-amber-400">
                              <CheckCircle2 className="h-4 w-4 inline mr-1" />
                              Customer baru dibuat di CRM
                            </p>
                          </div>
                        )}

                        <div className="p-3 rounded-lg bg-white/5 border border-border/30">
                          <Label className="text-xs text-muted-foreground">Conversation ID</Label>
                          <p className="text-sm font-mono text-amber-200">{testResult.result.conversation_id}</p>
                        </div>

                        {testResult.result.ai_response && (
                          <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30">
                            <Label className="text-xs text-green-400 mb-2 block">AI Response (Sent via WAHA)</Label>
                            <p className="text-sm text-green-100 whitespace-pre-wrap">{testResult.result.ai_response}</p>
                          </div>
                        )}

                        <div className="flex items-center gap-2">
                          <span className="text-sm text-red-300/60">WAHA Send Status:</span>
                          {testResult.result.waha_sent ? (
                            <Badge className="bg-green-500/20 text-green-400">Sent</Badge>
                          ) : (
                            <Badge className="bg-red-500/20 text-red-400">Failed</Badge>
                          )}
                        </div>
                      </div>
                    )}

                    {testResult.error && (
                      <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                        <p className="text-sm text-red-400">{testResult.error}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12 text-red-300/60">
                    <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Run a test to see results</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* System Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-amber-100 flex items-center gap-2">
                    <ScrollText className="h-5 w-5 text-amber-400" />
                    System Logs
                  </CardTitle>
                  <CardDescription className="text-red-300/60">WAHA integration activity logs</CardDescription>
                </div>
                <Button onClick={loadLogs} variant="outline" size="sm" className="border-red-900/30">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {logs.length === 0 ? (
                  <p className="text-center py-12 text-red-300/60">No logs yet</p>
                ) : (
                  logs.map((log) => (
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
                          <Badge className={getLogTypeColor(log.log_type)}>
                            {log.log_type?.replace('_', ' ')}
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
                      <p className="text-sm mt-2 text-red-200/80">{log.message}</p>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Config Tab */}
        <TabsContent value="config" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Current Config */}
            <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100 flex items-center gap-2">
                  <Wifi className="h-5 w-5 text-amber-400" />
                  Current WAHA Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {wahaConfig ? (
                  <>
                    <div className="p-3 rounded-lg bg-white/5 border border-border/30">
                      <Label className="text-xs text-muted-foreground">Base URL</Label>
                      <p className="text-sm font-mono text-amber-200 break-all">{wahaConfig.base_url}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/5 border border-border/30">
                      <Label className="text-xs text-muted-foreground">API Key</Label>
                      <p className="text-sm font-mono text-amber-200">{wahaConfig.api_key_preview || 'Not set'}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/5 border border-border/30">
                      <Label className="text-xs text-muted-foreground">Session</Label>
                      <p className="text-sm font-mono text-amber-200">{wahaConfig.session}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/5 border border-border/30">
                      <Label className="text-xs text-muted-foreground">Connection Status</Label>
                      {wahaStatus?.connected ? (
                        <Badge className="bg-green-500/20 text-green-400 mt-1">Connected</Badge>
                      ) : (
                        <Badge className="bg-red-500/20 text-red-400 mt-1">
                          Disconnected: {wahaStatus?.error || 'Check credentials'}
                        </Badge>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8 text-red-300/60">
                    <Loader2 className="h-8 w-8 mx-auto animate-spin mb-4" />
                    Loading config...
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Update Config */}
            <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100">Update WAHA Configuration</CardTitle>
                <CardDescription className="text-red-300/60">
                  Change WAHA server URL or API key
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleUpdateConfig} className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-red-200/80">New Base URL (optional)</Label>
                    <Input
                      value={newBaseUrl}
                      onChange={(e) => setNewBaseUrl(e.target.value)}
                      placeholder="https://waha-server.example.com"
                      className="bg-red-950/30 border-red-900/30 text-amber-50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-red-200/80">New API Key (optional)</Label>
                    <Input
                      type="password"
                      value={newApiKey}
                      onChange={(e) => setNewApiKey(e.target.value)}
                      placeholder="Enter new API key"
                      className="bg-red-950/30 border-red-900/30 text-amber-50"
                    />
                  </div>
                  <Button 
                    type="submit" 
                    disabled={updatingConfig || (!newBaseUrl && !newApiKey)}
                    className="w-full bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500"
                  >
                    {updatingConfig ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Updating...
                      </>
                    ) : (
                      'Update Configuration'
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
