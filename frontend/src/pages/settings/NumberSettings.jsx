import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Switch } from '../../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Badge } from '../../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Settings, Hash, FileText, Users, Package, RefreshCw, Eye, Save, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function NumberSettings() {
  const [transactionSettings, setTransactionSettings] = useState([]);
  const [masterSettings, setMasterSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editDialog, setEditDialog] = useState({ open: false, type: null, data: null });
  const [previewDialog, setPreviewDialog] = useState({ open: false, type: null, data: null });

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    try {
      const [txRes, masterRes] = await Promise.all([
        fetch(`${API}/api/number-settings/transactions`),
        fetch(`${API}/api/number-settings/masters`)
      ]);
      
      if (txRes.ok) {
        const txData = await txRes.json();
        setTransactionSettings(txData.items || []);
      }
      
      if (masterRes.ok) {
        const masterData = await masterRes.json();
        setMasterSettings(masterData.items || []);
      }
    } catch (error) {
      toast.error('Gagal memuat pengaturan nomor');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleEditTransaction = (setting) => {
    setEditDialog({ open: true, type: 'transaction', data: { ...setting } });
  };

  const handleEditMaster = (setting) => {
    setEditDialog({ open: true, type: 'master', data: { ...setting } });
  };

  const handleSaveTransaction = async () => {
    try {
      const { data } = editDialog;
      const res = await fetch(`${API}/api/number-settings/transactions/${data.module_code}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      
      if (res.ok) {
        toast.success('Pengaturan berhasil disimpan');
        setEditDialog({ open: false, type: null, data: null });
        fetchSettings();
      } else {
        toast.error('Gagal menyimpan pengaturan');
      }
    } catch (error) {
      toast.error('Error: ' + error.message);
    }
  };

  const handleSaveMaster = async () => {
    try {
      const { data } = editDialog;
      const res = await fetch(`${API}/api/number-settings/masters/${data.entity_type}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      
      if (res.ok) {
        toast.success('Pengaturan berhasil disimpan');
        setEditDialog({ open: false, type: null, data: null });
        fetchSettings();
      } else {
        toast.error('Gagal menyimpan pengaturan');
      }
    } catch (error) {
      toast.error('Error: ' + error.message);
    }
  };

  const handleResetCounter = async (moduleCode) => {
    if (!window.confirm(`Yakin reset counter ${moduleCode}? Nomor akan mulai dari awal.`)) return;
    
    try {
      const res = await fetch(`${API}/api/number-settings/transactions/${moduleCode}/reset`, {
        method: 'POST'
      });
      
      if (res.ok) {
        toast.success(`Counter ${moduleCode} berhasil direset`);
        fetchSettings();
      } else {
        toast.error('Gagal reset counter');
      }
    } catch (error) {
      toast.error('Error: ' + error.message);
    }
  };

  const handlePreview = async (type, code) => {
    try {
      const endpoint = type === 'transaction' 
        ? `${API}/api/number-settings/preview/transaction/${code}`
        : `${API}/api/number-settings/preview/master/${code}`;
      
      const res = await fetch(endpoint);
      if (res.ok) {
        const data = await res.json();
        setPreviewDialog({ open: true, type, data });
      }
    } catch (error) {
      toast.error('Gagal memuat preview');
    }
  };

  const handleGenerateTest = async (type, code) => {
    try {
      const endpoint = type === 'transaction'
        ? `${API}/api/number-settings/generate/transaction`
        : `${API}/api/number-settings/generate/master?entity_type=${code}`;
      
      const options = type === 'transaction' 
        ? {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ module_code: code })
          }
        : { method: 'POST' };
      
      const res = await fetch(endpoint, options);
      if (res.ok) {
        const data = await res.json();
        toast.success(`Generated: ${data.number || data.code}`);
        fetchSettings();
      }
    } catch (error) {
      toast.error('Gagal generate nomor');
    }
  };

  const getResetTypeLabel = (type) => {
    switch (type) {
      case 'monthly': return 'Bulanan';
      case 'yearly': return 'Tahunan';
      case 'none': return 'Tidak Reset';
      default: return type;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="number-settings-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Settings className="w-6 h-6" />
            Pengaturan Nomor
          </h1>
          <p className="text-gray-600">Engine terpusat untuk auto numbering transaksi dan master data</p>
        </div>
        <Button onClick={fetchSettings} variant="outline" data-testid="refresh-btn">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="transaction" className="w-full">
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="transaction" data-testid="tab-transaction">
            <FileText className="w-4 h-4 mr-2" />
            Nomor Transaksi
          </TabsTrigger>
          <TabsTrigger value="master" data-testid="tab-master">
            <Users className="w-4 h-4 mr-2" />
            Nomor Master
          </TabsTrigger>
        </TabsList>

        {/* Transaction Number Settings */}
        <TabsContent value="transaction" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Hash className="w-5 h-5" />
                Pengaturan Nomor Transaksi
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-slate-800/50">
                      <th className="text-left p-3">Modul</th>
                      <th className="text-left p-3">Nama</th>
                      <th className="text-left p-3">Format</th>
                      <th className="text-center p-3">Preview</th>
                      <th className="text-center p-3">Reset</th>
                      <th className="text-center p-3">Status</th>
                      <th className="text-center p-3">Aksi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactionSettings.map((setting) => (
                      <tr key={setting.module_code} className="border-b hover:bg-slate-800/50">
                        <td className="p-3">
                          <Badge variant="outline">{setting.module_code}</Badge>
                        </td>
                        <td className="p-3">{setting.module_name}</td>
                        <td className="p-3 font-mono text-xs">
                          {setting.prefix_1}
                          {setting.separator}
                          {setting.include_date ? `{DATE}${setting.separator}` : ''}
                          {'0'.repeat(setting.digit_count)}
                        </td>
                        <td className="p-3 text-center">
                          <code className="bg-blue-50 px-2 py-1 rounded text-blue-700">
                            {setting.preview}
                          </code>
                        </td>
                        <td className="p-3 text-center">
                          <Badge variant={setting.reset_type === 'none' ? 'secondary' : 'default'}>
                            {getResetTypeLabel(setting.reset_type)}
                          </Badge>
                        </td>
                        <td className="p-3 text-center">
                          {setting.is_active ? (
                            <Badge className="bg-green-500">Aktif</Badge>
                          ) : (
                            <Badge variant="destructive">Nonaktif</Badge>
                          )}
                        </td>
                        <td className="p-3 text-center space-x-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handlePreview('transaction', setting.module_code)}
                            title="Preview"
                            data-testid={`preview-${setting.module_code}`}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEditTransaction(setting)}
                            title="Edit"
                            data-testid={`edit-${setting.module_code}`}
                          >
                            <Settings className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleResetCounter(setting.module_code)}
                            title="Reset Counter"
                            className="text-red-600 hover:text-red-700"
                            data-testid={`reset-${setting.module_code}`}
                          >
                            <RefreshCw className="w-4 h-4" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Master Number Settings */}
        <TabsContent value="master" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="w-5 h-5" />
                Pengaturan Kode Master
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-slate-800/50">
                      <th className="text-left p-3">Entity</th>
                      <th className="text-left p-3">Nama</th>
                      <th className="text-left p-3">Prefix</th>
                      <th className="text-center p-3">Digit</th>
                      <th className="text-center p-3">Preview</th>
                      <th className="text-center p-3">Status</th>
                      <th className="text-center p-3">Aksi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {masterSettings.map((setting) => (
                      <tr key={setting.entity_type} className="border-b hover:bg-slate-800/50">
                        <td className="p-3">
                          <Badge variant="outline">{setting.entity_type}</Badge>
                        </td>
                        <td className="p-3">{setting.entity_name}</td>
                        <td className="p-3 font-mono">{setting.prefix}</td>
                        <td className="p-3 text-center">{setting.digit_count}</td>
                        <td className="p-3 text-center">
                          <code className="bg-green-50 px-2 py-1 rounded text-green-700">
                            {setting.preview}
                          </code>
                        </td>
                        <td className="p-3 text-center">
                          {setting.is_active ? (
                            <Badge className="bg-green-500">Aktif</Badge>
                          ) : (
                            <Badge variant="destructive">Nonaktif</Badge>
                          )}
                        </td>
                        <td className="p-3 text-center space-x-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handlePreview('master', setting.entity_type)}
                            title="Preview"
                            data-testid={`preview-${setting.entity_type}`}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEditMaster(setting)}
                            title="Edit"
                            data-testid={`edit-${setting.entity_type}`}
                          >
                            <Settings className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleGenerateTest('master', setting.entity_type)}
                            title="Generate Test"
                            data-testid={`generate-${setting.entity_type}`}
                          >
                            <Hash className="w-4 h-4" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Transaction Dialog */}
      <Dialog open={editDialog.open && editDialog.type === 'transaction'} onOpenChange={(open) => !open && setEditDialog({ open: false, type: null, data: null })}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Pengaturan Nomor Transaksi</DialogTitle>
          </DialogHeader>
          {editDialog.data && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Kode Modul</Label>
                  <Input value={editDialog.data.module_code} disabled />
                </div>
                <div>
                  <Label>Nama Modul</Label>
                  <Input 
                    value={editDialog.data.module_name} 
                    onChange={(e) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, module_name: e.target.value }
                    }))}
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Prefix 1</Label>
                  <Input 
                    value={editDialog.data.prefix_1} 
                    onChange={(e) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, prefix_1: e.target.value }
                    }))}
                  />
                </div>
                <div>
                  <Label>Prefix 2</Label>
                  <Input 
                    value={editDialog.data.prefix_2 || ''} 
                    onChange={(e) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, prefix_2: e.target.value }
                    }))}
                    placeholder="Opsional"
                  />
                </div>
                <div>
                  <Label>Prefix 3</Label>
                  <Input 
                    value={editDialog.data.prefix_3 || ''} 
                    onChange={(e) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, prefix_3: e.target.value }
                    }))}
                    placeholder="Opsional"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Separator</Label>
                  <Select 
                    value={editDialog.data.separator} 
                    onValueChange={(val) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, separator: val }
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="-">- (Dash)</SelectItem>
                      <SelectItem value="/">/  (Slash)</SelectItem>
                      <SelectItem value=".">. (Dot)</SelectItem>
                      <SelectItem value="">Tanpa Separator</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Jumlah Digit</Label>
                  <Select 
                    value={String(editDialog.data.digit_count)} 
                    onValueChange={(val) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, digit_count: parseInt(val) }
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="3">3 digit</SelectItem>
                      <SelectItem value="4">4 digit</SelectItem>
                      <SelectItem value="5">5 digit</SelectItem>
                      <SelectItem value="6">6 digit</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Format Tanggal</Label>
                  <Select 
                    value={editDialog.data.date_format} 
                    onValueChange={(val) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, date_format: val }
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="YYYYMMDD">YYYYMMDD</SelectItem>
                      <SelectItem value="YYYYMM">YYYYMM</SelectItem>
                      <SelectItem value="YYYY">YYYY</SelectItem>
                      <SelectItem value="MMDD">MMDD</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Reset Nomor</Label>
                  <Select 
                    value={editDialog.data.reset_type} 
                    onValueChange={(val) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, reset_type: val }
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="monthly">Bulanan</SelectItem>
                      <SelectItem value="yearly">Tahunan</SelectItem>
                      <SelectItem value="none">Tidak Reset</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Switch 
                    checked={editDialog.data.include_date} 
                    onCheckedChange={(checked) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, include_date: checked }
                    }))}
                  />
                  <Label>Sertakan Tanggal</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch 
                    checked={editDialog.data.is_active} 
                    onCheckedChange={(checked) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, is_active: checked }
                    }))}
                  />
                  <Label>Aktif</Label>
                </div>
              </div>
              
              <div className="p-4 bg-blue-50 rounded-lg">
                <Label className="text-blue-700">Preview Contoh Nomor:</Label>
                <div className="text-2xl font-mono text-blue-900 mt-2">
                  {editDialog.data.preview || 'Loading...'}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialog({ open: false, type: null, data: null })}>
              Batal
            </Button>
            <Button onClick={handleSaveTransaction} data-testid="save-transaction-btn">
              <Save className="w-4 h-4 mr-2" />
              Simpan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Master Dialog */}
      <Dialog open={editDialog.open && editDialog.type === 'master'} onOpenChange={(open) => !open && setEditDialog({ open: false, type: null, data: null })}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Pengaturan Kode Master</DialogTitle>
          </DialogHeader>
          {editDialog.data && (
            <div className="space-y-4 py-4">
              <div>
                <Label>Tipe Entity</Label>
                <Input value={editDialog.data.entity_type} disabled />
              </div>
              <div>
                <Label>Nama Entity</Label>
                <Input 
                  value={editDialog.data.entity_name} 
                  onChange={(e) => setEditDialog(prev => ({
                    ...prev,
                    data: { ...prev.data, entity_name: e.target.value }
                  }))}
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Prefix</Label>
                  <Input 
                    value={editDialog.data.prefix} 
                    onChange={(e) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, prefix: e.target.value }
                    }))}
                  />
                </div>
                <div>
                  <Label>Separator</Label>
                  <Select 
                    value={editDialog.data.separator} 
                    onValueChange={(val) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, separator: val }
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="-">-</SelectItem>
                      <SelectItem value="/">/</SelectItem>
                      <SelectItem value=".">.</SelectItem>
                      <SelectItem value="">Tidak ada</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Digit</Label>
                  <Select 
                    value={String(editDialog.data.digit_count)} 
                    onValueChange={(val) => setEditDialog(prev => ({
                      ...prev,
                      data: { ...prev.data, digit_count: parseInt(val) }
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="3">3</SelectItem>
                      <SelectItem value="4">4</SelectItem>
                      <SelectItem value="5">5</SelectItem>
                      <SelectItem value="6">6</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <Switch 
                  checked={editDialog.data.is_active} 
                  onCheckedChange={(checked) => setEditDialog(prev => ({
                    ...prev,
                    data: { ...prev.data, is_active: checked }
                  }))}
                />
                <Label>Aktif</Label>
              </div>
              
              <div className="p-4 bg-green-50 rounded-lg">
                <Label className="text-green-700">Preview Contoh Kode:</Label>
                <div className="text-2xl font-mono text-green-900 mt-2">
                  {editDialog.data.preview || 'Loading...'}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialog({ open: false, type: null, data: null })}>
              Batal
            </Button>
            <Button onClick={handleSaveMaster} data-testid="save-master-btn">
              <Save className="w-4 h-4 mr-2" />
              Simpan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog open={previewDialog.open} onOpenChange={(open) => !open && setPreviewDialog({ open: false, type: null, data: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Preview Nomor Berikutnya</DialogTitle>
          </DialogHeader>
          {previewDialog.data && (
            <div className="py-4 text-center">
              <div className="p-6 bg-slate-700/50 rounded-lg">
                <div className="text-3xl font-mono font-bold text-gray-900">
                  {previewDialog.data.preview}
                </div>
                <div className="text-sm text-gray-500 mt-2">
                  Sequence: #{previewDialog.data.next_sequence}
                </div>
              </div>
              <div className="mt-4 flex gap-2 justify-center">
                <Button 
                  onClick={() => {
                    handleGenerateTest(
                      previewDialog.type, 
                      previewDialog.type === 'transaction' 
                        ? previewDialog.data.setting.module_code 
                        : previewDialog.data.setting.entity_type
                    );
                    setPreviewDialog({ open: false, type: null, data: null });
                  }}
                  data-testid="generate-number-btn"
                >
                  <Hash className="w-4 h-4 mr-2" />
                  Generate Nomor Ini
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Info Card */}
      <Card className="bg-amber-50 border-amber-200">
        <CardContent className="pt-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
            <div className="text-sm text-amber-800">
              <p className="font-semibold">Penting:</p>
              <ul className="list-disc ml-4 mt-1 space-y-1">
                <li>Semua modul transaksi wajib menggunakan engine ini untuk generate nomor</li>
                <li>Reset counter hanya dilakukan jika benar-benar diperlukan</li>
                <li>Perubahan format akan berlaku untuk nomor baru, tidak mengubah nomor lama</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
