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
import { 
  MessageSquare, Bot, Send, Copy, Sparkles, Users,
  Package, FileText, Plus, RefreshCw, AlertCircle,
  CheckCircle, Megaphone
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const CRMAI = () => {
  const [loading, setLoading] = useState(false);
  const [prompts, setPrompts] = useState([]);
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [customerName, setCustomerName] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [complaintText, setComplaintText] = useState('');
  const [generatedReply, setGeneratedReply] = useState('');
  const [complaintAnalysis, setComplaintAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [marketingScript, setMarketingScript] = useState('');

  useEffect(() => {
    fetchPrompts();
  }, []);

  const fetchPrompts = async () => {
    try {
      const res = await axios.get(`${API}/api/crm-ai/prompts`);
      setPrompts(res.data.prompts || []);
    } catch (err) {
      console.error('Error fetching prompts:', err);
    }
  };

  const seedPrompts = async () => {
    try {
      await axios.post(`${API}/api/crm-ai/seed-prompts`);
      toast.success('Prompt templates berhasil dibuat');
      fetchPrompts();
    } catch (err) {
      toast.error('Gagal membuat prompts');
    }
  };

  const generateReply = async () => {
    if (!selectedPrompt || !customerName) {
      toast.error('Pilih prompt dan masukkan nama customer');
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/crm-ai/chat/generate-reply`, {
        prompt_id: selectedPrompt,
        customer_id: customerId || 'guest',
        customer_name: customerName,
        context: {}
      });
      setGeneratedReply(res.data.generated_reply);
      toast.success('Reply berhasil di-generate');
    } catch (err) {
      toast.error('Gagal generate reply');
    } finally {
      setLoading(false);
    }
  };

  const analyzeComplaint = async () => {
    if (!complaintText) {
      toast.error('Masukkan teks komplain');
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/crm-ai/complaint/analyze?complaint_text=${encodeURIComponent(complaintText)}&customer_id=${customerId}`);
      setComplaintAnalysis(res.data);
      toast.success('Komplain berhasil dianalisis');
    } catch (err) {
      toast.error('Gagal menganalisis komplain');
    } finally {
      setLoading(false);
    }
  };

  const getRecommendations = async () => {
    if (!customerId) {
      toast.error('Masukkan Customer ID');
      return;
    }

    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/crm-ai/recommend-products/${customerId}`);
      setRecommendations(res.data);
    } catch (err) {
      toast.error('Gagal mendapatkan rekomendasi');
    } finally {
      setLoading(false);
    }
  };

  const generateMarketingScript = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/crm-ai/marketing-scripts/generate?campaign_type=promo`, ['sample-product-1']);
      setMarketingScript(res.data.generated_script);
    } catch (err) {
      toast.error('Gagal generate script');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Disalin ke clipboard');
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'customer_reply': return 'bg-blue-600';
      case 'marketing_script': return 'bg-green-600';
      case 'complaint_handling': return 'bg-red-600';
      case 'product_recommendation': return 'bg-purple-600';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0608] to-[#1a0a0e] p-4" data-testid="crm-ai-page">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
              <Bot className="h-6 w-6 text-cyan-400" />
              CRM AI Prompt Builder
            </h1>
            <p className="text-sm text-gray-400">Buat & kelola prompt AI untuk interaksi customer</p>
          </div>
          <Button 
            onClick={seedPrompts}
            className="bg-cyan-900/50 hover:bg-cyan-800/50"
          >
            <Plus className="h-4 w-4 mr-1" />
            Generate Default Prompts
          </Button>
        </div>
      </div>

      <Tabs defaultValue="reply-generator" className="space-y-4">
        <TabsList className="bg-red-950/50 p-1">
          <TabsTrigger value="reply-generator" className="data-[state=active]:bg-red-900/50">
            <MessageSquare className="h-4 w-4 mr-1" />
            Reply Generator
          </TabsTrigger>
          <TabsTrigger value="complaint" className="data-[state=active]:bg-red-900/50">
            <AlertCircle className="h-4 w-4 mr-1" />
            Komplain Handler
          </TabsTrigger>
          <TabsTrigger value="recommendations" className="data-[state=active]:bg-red-900/50">
            <Package className="h-4 w-4 mr-1" />
            Product Recommendations
          </TabsTrigger>
          <TabsTrigger value="marketing" className="data-[state=active]:bg-red-900/50">
            <Megaphone className="h-4 w-4 mr-1" />
            Marketing Scripts
          </TabsTrigger>
          <TabsTrigger value="templates" className="data-[state=active]:bg-red-900/50">
            <FileText className="h-4 w-4 mr-1" />
            Templates
          </TabsTrigger>
        </TabsList>

        {/* Reply Generator */}
        <TabsContent value="reply-generator">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="bg-[#120a0c]/80 border-cyan-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm">Generate Customer Reply</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400">Template Prompt</label>
                  <Select onValueChange={setSelectedPrompt}>
                    <SelectTrigger className="bg-red-950/50 border-red-700/30">
                      <SelectValue placeholder="Pilih template..." />
                    </SelectTrigger>
                    <SelectContent>
                      {prompts.filter(p => p.category === 'customer_reply').map((p) => (
                        <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs text-gray-400">Nama Customer</label>
                  <Input
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    placeholder="Nama customer..."
                    className="bg-red-950/50 border-red-700/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Customer ID (opsional)</label>
                  <Input
                    value={customerId}
                    onChange={(e) => setCustomerId(e.target.value)}
                    placeholder="ID customer..."
                    className="bg-red-950/50 border-red-700/30"
                  />
                </div>
                <Button 
                  onClick={generateReply}
                  disabled={loading}
                  className="w-full bg-cyan-900/50 hover:bg-cyan-800/50"
                >
                  {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Sparkles className="h-4 w-4 mr-1" />}
                  Generate Reply
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-green-900/30">
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-amber-100 text-sm">Generated Reply</CardTitle>
                {generatedReply && (
                  <Button size="sm" variant="ghost" onClick={() => copyToClipboard(generatedReply)}>
                    <Copy className="h-4 w-4" />
                  </Button>
                )}
              </CardHeader>
              <CardContent>
                {generatedReply ? (
                  <div className="p-3 bg-green-900/20 rounded-lg border border-green-700/30 whitespace-pre-wrap">
                    {generatedReply}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <MessageSquare className="h-10 w-10 mx-auto text-gray-600 mb-2" />
                    <p className="text-gray-400 text-sm">Reply akan muncul di sini</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Complaint Handler */}
        <TabsContent value="complaint">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="bg-[#120a0c]/80 border-orange-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm">Analisis Komplain</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400">Teks Komplain dari Customer</label>
                  <Textarea
                    value={complaintText}
                    onChange={(e) => setComplaintText(e.target.value)}
                    placeholder="Paste komplain customer di sini..."
                    className="bg-red-950/50 border-red-700/30 min-h-[120px]"
                  />
                </div>
                <Button 
                  onClick={analyzeComplaint}
                  disabled={loading}
                  className="w-full bg-orange-900/50 hover:bg-orange-800/50"
                >
                  {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Bot className="h-4 w-4 mr-1" />}
                  Analisis Komplain
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-blue-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm">Hasil Analisis</CardTitle>
              </CardHeader>
              <CardContent>
                {complaintAnalysis ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Badge className={complaintAnalysis.priority === 'high' ? 'bg-red-600' : 'bg-yellow-600'}>
                        {complaintAnalysis.priority}
                      </Badge>
                      <Badge variant="outline">{complaintAnalysis.detected_category}</Badge>
                    </div>
                    <div className="p-3 bg-blue-900/20 rounded-lg border border-blue-700/30">
                      <p className="text-xs text-blue-300 mb-1">Suggested Response:</p>
                      <p className="text-sm text-amber-100 whitespace-pre-wrap">{complaintAnalysis.suggested_response}</p>
                    </div>
                    <div className="p-2 bg-green-900/20 rounded border border-green-700/30">
                      <p className="text-xs text-green-300">{complaintAnalysis.recommended_action}</p>
                    </div>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => copyToClipboard(complaintAnalysis.suggested_response)}
                      className="w-full"
                    >
                      <Copy className="h-4 w-4 mr-1" />
                      Copy Response
                    </Button>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <AlertCircle className="h-10 w-10 mx-auto text-gray-600 mb-2" />
                    <p className="text-gray-400 text-sm">Hasil analisis akan muncul di sini</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Product Recommendations */}
        <TabsContent value="recommendations">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="bg-[#120a0c]/80 border-purple-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm">Get Product Recommendations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400">Customer ID</label>
                  <Input
                    value={customerId}
                    onChange={(e) => setCustomerId(e.target.value)}
                    placeholder="Masukkan Customer ID..."
                    className="bg-red-950/50 border-red-700/30"
                  />
                </div>
                <Button 
                  onClick={getRecommendations}
                  disabled={loading}
                  className="w-full bg-purple-900/50 hover:bg-purple-800/50"
                >
                  {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Package className="h-4 w-4 mr-1" />}
                  Get Recommendations
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-green-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm">
                  Recommended Products ({recommendations?.total_recommendations || 0})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {recommendations?.recommendations?.length > 0 ? (
                  <div className="space-y-2 max-h-[300px] overflow-y-auto">
                    {recommendations.recommendations.map((rec, idx) => (
                      <div key={idx} className="p-2 bg-green-900/20 rounded border border-green-700/30">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="text-sm font-medium text-amber-100">{rec.name}</p>
                            <p className="text-xs text-gray-400">{rec.category}</p>
                          </div>
                          <p className="text-sm text-green-400">Rp {rec.price?.toLocaleString()}</p>
                        </div>
                        <p className="text-xs text-blue-300 mt-1">{rec.reason}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Package className="h-10 w-10 mx-auto text-gray-600 mb-2" />
                    <p className="text-gray-400 text-sm">Rekomendasi akan muncul di sini</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Marketing Scripts */}
        <TabsContent value="marketing">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="bg-[#120a0c]/80 border-pink-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm">Generate Marketing Script</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  onClick={generateMarketingScript}
                  disabled={loading}
                  className="w-full bg-pink-900/50 hover:bg-pink-800/50"
                >
                  {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Megaphone className="h-4 w-4 mr-1" />}
                  Generate Promo Script
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-[#120a0c]/80 border-green-900/30">
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-amber-100 text-sm">Generated Script</CardTitle>
                {marketingScript && (
                  <Button size="sm" variant="ghost" onClick={() => copyToClipboard(marketingScript)}>
                    <Copy className="h-4 w-4" />
                  </Button>
                )}
              </CardHeader>
              <CardContent>
                {marketingScript ? (
                  <div className="p-3 bg-pink-900/20 rounded-lg border border-pink-700/30 whitespace-pre-wrap text-sm">
                    {marketingScript}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Megaphone className="h-10 w-10 mx-auto text-gray-600 mb-2" />
                    <p className="text-gray-400 text-sm">Script akan muncul di sini</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Templates */}
        <TabsContent value="templates">
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Prompt Templates ({prompts.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {prompts.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {prompts.map((p) => (
                    <div key={p.id} className="p-3 bg-red-950/30 rounded-lg border border-red-900/30">
                      <div className="flex items-start justify-between mb-2">
                        <p className="font-medium text-amber-100">{p.name}</p>
                        <Badge className={getCategoryColor(p.category)} size="sm">{p.category}</Badge>
                      </div>
                      <p className="text-xs text-gray-400 mb-2">{p.description}</p>
                      <div className="p-2 bg-black/30 rounded text-xs text-gray-300 font-mono max-h-[80px] overflow-y-auto">
                        {p.prompt_template}
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
                        <span>Variables: {p.variables?.join(', ') || '-'}</span>
                        <span>•</span>
                        <span>Used: {p.usage_count || 0}x</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 mx-auto text-gray-600 mb-2" />
                  <p className="text-gray-400">Belum ada template</p>
                  <Button onClick={seedPrompts} className="mt-2 bg-red-900/50">
                    Generate Default Templates
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CRMAI;
