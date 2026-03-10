import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { 
  Upload, Download, FileSpreadsheet, CheckCircle, XCircle,
  AlertCircle, RefreshCw, History, Undo2, Eye, FileJson,
  FileText, Database, Users, Package
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const ImportSystem = () => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [importing, setImporting] = useState(false);
  const [history, setHistory] = useState([]);
  const [updateExisting, setUpdateExisting] = useState(true);
  const [skipErrors, setSkipErrors] = useState(true);

  useEffect(() => {
    fetchTemplates();
    fetchHistory();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await axios.get(`${API}/api/import/templates`);
      setTemplates(res.data.templates || []);
    } catch (err) {
      console.error('Error:', err);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API}/api/import/history`);
      setHistory(res.data.imports || []);
    } catch (err) {
      console.error('Error:', err);
    }
  };

  const downloadTemplate = async (templateKey) => {
    try {
      const response = await fetch(`${API}/api/import/templates/${templateKey}/download?format=xlsx`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `template_${templateKey}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      toast.success('Template berhasil didownload');
    } catch (err) {
      toast.error('Gagal download template');
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setPreview(null);
  };

  const previewImport = async () => {
    if (!selectedTemplate || !file) {
      toast.error('Pilih template dan file');
      return;
    }

    setImporting(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await axios.post(`${API}/api/import/preview/${selectedTemplate}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setPreview(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal preview data');
    } finally {
      setImporting(false);
    }
  };

  const executeImport = async () => {
    if (!selectedTemplate || !file) {
      toast.error('Pilih template dan file');
      return;
    }

    setImporting(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('update_existing', updateExisting);
      formData.append('skip_errors', skipErrors);

      const res = await axios.post(`${API}/api/import/execute/${selectedTemplate}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (res.data.status === 'completed') {
        toast.success(`Import berhasil! ${res.data.results.inserted} data ditambahkan`);
      } else if (res.data.status === 'partial') {
        toast.warning(`Import partial: ${res.data.results.inserted} sukses, ${res.data.results.failed} gagal`);
      } else {
        toast.error('Import gagal');
      }

      setPreview(null);
      setFile(null);
      fetchHistory();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal import data');
    } finally {
      setImporting(false);
    }
  };

  const rollbackImport = async (importId) => {
    try {
      await axios.post(`${API}/api/import/rollback/${importId}`);
      toast.success('Rollback berhasil');
      fetchHistory();
    } catch (err) {
      toast.error('Gagal rollback');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed': return <Badge className="bg-green-600">Completed</Badge>;
      case 'partial': return <Badge className="bg-yellow-600">Partial</Badge>;
      case 'failed': return <Badge className="bg-red-600">Failed</Badge>;
      case 'rolled_back': return <Badge className="bg-gray-600">Rolled Back</Badge>;
      default: return <Badge>{status}</Badge>;
    }
  };

  const getTemplateIcon = (key) => {
    if (key.includes('product')) return <Package className="h-4 w-4" />;
    if (key.includes('employee') || key.includes('customer') || key.includes('supplier')) return <Users className="h-4 w-4" />;
    return <Database className="h-4 w-4" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0608] to-[#1a0a0e] p-4" data-testid="import-system-page">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
          <Upload className="h-6 w-6 text-green-400" />
          Import Data System
        </h1>
        <p className="text-sm text-gray-400">Import data dari Excel, CSV, atau JSON dengan validasi</p>
      </div>

      <Tabs defaultValue="import" className="space-y-4">
        <TabsList className="bg-red-950/50 p-1">
          <TabsTrigger value="import" className="data-[state=active]:bg-red-900/50">
            <Upload className="h-4 w-4 mr-1" />
            Import Data
          </TabsTrigger>
          <TabsTrigger value="templates" className="data-[state=active]:bg-red-900/50">
            <FileSpreadsheet className="h-4 w-4 mr-1" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-red-900/50">
            <History className="h-4 w-4 mr-1" />
            History
          </TabsTrigger>
        </TabsList>

        {/* Import Tab */}
        <TabsContent value="import">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Upload Form */}
            <Card className="bg-[#120a0c]/80 border-green-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100 text-sm">Upload File</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs text-gray-400">Template Import</label>
                  <Select onValueChange={setSelectedTemplate}>
                    <SelectTrigger className="bg-red-950/50 border-red-700/30">
                      <SelectValue placeholder="Pilih template..." />
                    </SelectTrigger>
                    <SelectContent>
                      {templates.map((t) => (
                        <SelectItem key={t.key} value={t.key}>
                          <div className="flex items-center gap-2">
                            {getTemplateIcon(t.key)}
                            {t.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-xs text-gray-400">File (Excel, CSV, JSON)</label>
                  <Input
                    type="file"
                    accept=".xlsx,.xls,.csv,.json"
                    onChange={handleFileChange}
                    className="bg-red-950/50 border-red-700/30"
                  />
                  {file && (
                    <p className="text-xs text-green-400 mt-1">File: {file.name}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Checkbox 
                      id="update" 
                      checked={updateExisting}
                      onCheckedChange={setUpdateExisting}
                    />
                    <label htmlFor="update" className="text-xs text-gray-400">
                      Update data existing (jika duplikat)
                    </label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox 
                      id="skip" 
                      checked={skipErrors}
                      onCheckedChange={setSkipErrors}
                    />
                    <label htmlFor="skip" className="text-xs text-gray-400">
                      Skip baris error (lanjutkan import)
                    </label>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={previewImport}
                    disabled={importing || !selectedTemplate || !file}
                    className="flex-1 bg-blue-900/50 hover:bg-blue-800/50"
                  >
                    {importing ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Eye className="h-4 w-4 mr-1" />}
                    Preview
                  </Button>
                  <Button
                    onClick={executeImport}
                    disabled={importing || !preview?.valid}
                    className="flex-1 bg-green-900/50 hover:bg-green-800/50"
                  >
                    {importing ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Upload className="h-4 w-4 mr-1" />}
                    Import
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Preview Results */}
            <Card className="bg-[#120a0c]/80 border-blue-900/30">
              <CardHeader>
                <CardTitle className="text-amber-100 text-sm flex items-center justify-between">
                  Preview Data
                  {preview && (
                    <div className="flex gap-2">
                      <Badge className={preview.valid ? 'bg-green-600' : 'bg-red-600'}>
                        {preview.valid ? 'Valid' : 'Ada Error'}
                      </Badge>
                    </div>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {preview ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-4 gap-2 text-center">
                      <div className="p-2 bg-green-900/20 rounded">
                        <p className="text-lg font-bold text-green-400">{preview.valid_rows}</p>
                        <p className="text-xs text-gray-400">Valid</p>
                      </div>
                      <div className="p-2 bg-red-900/20 rounded">
                        <p className="text-lg font-bold text-red-400">{preview.invalid_rows}</p>
                        <p className="text-xs text-gray-400">Invalid</p>
                      </div>
                      <div className="p-2 bg-yellow-900/20 rounded">
                        <p className="text-lg font-bold text-yellow-400">{preview.duplicate_rows}</p>
                        <p className="text-xs text-gray-400">Duplikat</p>
                      </div>
                      <div className="p-2 bg-blue-900/20 rounded">
                        <p className="text-lg font-bold text-blue-400">{preview.total_rows}</p>
                        <p className="text-xs text-gray-400">Total</p>
                      </div>
                    </div>

                    <div className="max-h-[300px] overflow-y-auto space-y-1">
                      {preview.preview?.slice(0, 20).map((row, i) => (
                        <div 
                          key={i}
                          className={`p-2 rounded text-xs flex items-center gap-2 ${
                            row.status === 'valid' ? 'bg-green-900/20' :
                            row.status === 'invalid' ? 'bg-red-900/20' :
                            'bg-yellow-900/20'
                          }`}
                        >
                          {row.status === 'valid' ? (
                            <CheckCircle className="h-4 w-4 text-green-400" />
                          ) : row.status === 'invalid' ? (
                            <XCircle className="h-4 w-4 text-red-400" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-yellow-400" />
                          )}
                          <span className="text-gray-400">Baris {row.row}:</span>
                          <span className="text-amber-100 truncate flex-1">
                            {JSON.stringify(row.data).slice(0, 50)}...
                          </span>
                          {row.errors && (
                            <span className="text-red-400">{row.errors[0]}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Eye className="h-10 w-10 mx-auto text-gray-600 mb-2" />
                    <p className="text-gray-400 text-sm">Preview data akan muncul di sini</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates">
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader>
              <CardTitle className="text-amber-100">Template Import</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {templates.map((t) => (
                  <div key={t.key} className="p-3 bg-red-950/30 rounded-lg border border-red-900/30">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getTemplateIcon(t.key)}
                        <p className="font-medium text-amber-100">{t.name}</p>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => downloadTemplate(t.key)}
                        className="h-7"
                      >
                        <Download className="h-3 w-3 mr-1" />
                        Download
                      </Button>
                    </div>
                    <div className="text-xs text-gray-400">
                      <p><span className="text-red-400">Wajib:</span> {t.required_columns.join(', ')}</p>
                      {t.optional_columns.length > 0 && (
                        <p><span className="text-gray-500">Opsional:</span> {t.optional_columns.join(', ')}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-amber-100">Import History</CardTitle>
              <Button size="sm" variant="outline" onClick={fetchHistory}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {history.map((item) => (
                  <div key={item.id} className="p-3 bg-red-950/20 rounded-lg border border-red-900/20 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-amber-100">{item.template}</p>
                        {getStatusBadge(item.status)}
                      </div>
                      <p className="text-xs text-gray-400">{item.filename}</p>
                      <p className="text-xs text-gray-500">
                        {item.results?.inserted || 0} inserted, {item.results?.updated || 0} updated, {item.results?.failed || 0} failed
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <p className="text-xs text-gray-400">{new Date(item.started_at).toLocaleString('id-ID')}</p>
                      {item.status !== 'rolled_back' && item.results?.inserted > 0 && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => rollbackImport(item.id)}
                          className="h-7 text-red-400"
                        >
                          <Undo2 className="h-3 w-3 mr-1" />
                          Rollback
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
                {history.length === 0 && (
                  <p className="text-center text-gray-400 py-4">Belum ada history import</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ImportSystem;
