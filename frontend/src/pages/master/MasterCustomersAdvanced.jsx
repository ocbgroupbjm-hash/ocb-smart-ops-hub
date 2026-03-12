import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Switch } from '../../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Badge } from '../../components/ui/badge';
import { Plus, Search, Edit2, Trash2, Loader2, Phone, Mail, Star, User, CreditCard, FileText, Building, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const MasterCustomersAdvanced = () => {
  const { api } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [groups, setGroups] = useState([]);
  const [salesPersons, setSalesPersons] = useState([]);
  const [regions, setRegions] = useState([]);
  const [saving, setSaving] = useState(false);
  
  // Form data dengan field lengkap
  const [formData, setFormData] = useState({
    // Data Umum
    code: 'AUTO',
    code_mode: 'auto',
    name: '',
    group_id: '',
    address: '',
    city: '',
    province: '',
    country: 'Indonesia',
    postal_code: '',
    phone: '',
    fax: '',
    email: '',
    contact_person: '',
    birth_date: '',
    region_id: '',
    sub_region_id: '',
    salesperson_id: '',
    notes: '',
    is_active: true,
    
    // Data Kredit/Piutang
    can_credit: true,
    credit_limit: 0,
    credit_days_limit: 30,
    default_due_days: 30,
    max_credit_per_invoice: 0,
    include_pending_checks: false,
    default_discount_type: 'none',
    branch_credit_limit: 0,
    
    // Data Pajak
    use_tax: true,
    tax_type: 'default',
    tax_value: 11,
    id_type: 'npwp',
    npwp: '',
    nik: '',
    passport: '',
    other_doc: '',
    nitku: '',
    npwp_name: '',
    npwp_address: '',
    tax_country: 'Indonesia',
    
    // Data Keuangan/Bank
    bank_account_no: '',
    bank_account_name: '',
    bank_name: '',
    default_ar_account: '',
    default_payment_term: 'net30',
    
    // Points
    points: 0
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [res, groupRes, salesRes, regionRes] = await Promise.all([
        api(`/api/customers?search=${searchTerm}`),
        api('/api/master/customer-groups'),
        api('/api/master/sales-persons'),
        api('/api/master/regions')
      ]);
      if (res.ok) {
        const data = await res.json();
        setItems(data.items || data || []);
      }
      if (groupRes.ok) setGroups(await groupRes.json());
      if (salesRes.ok) setSalesPersons((await salesRes.json()).items || []);
      if (regionRes.ok) setRegions((await regionRes.json()).items || []);
    } catch (err) { 
      console.error(err);
      toast.error('Gagal memuat data'); 
    }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Nama pelanggan wajib diisi');
      return;
    }
    
    setSaving(true);
    try {
      // Generate auto code if needed
      let finalCode = formData.code;
      if (formData.code === 'AUTO') {
        const genRes = await fetch(`${API}/api/number-settings/generate/master?entity_type=customer`, {
          method: 'POST'
        });
        if (genRes.ok) {
          const genData = await genRes.json();
          finalCode = genData.code;
        } else {
          throw new Error('Gagal generate kode otomatis');
        }
      }
      
      const payload = { ...formData, code: finalCode };
      const url = editingItem ? `/api/customers/${editingItem.id}` : '/api/customers';
      const res = await api(url, { 
        method: editingItem ? 'PUT' : 'POST', 
        body: JSON.stringify(payload) 
      });
      
      if (res.ok) { 
        toast.success(`Customer ${finalCode} berhasil disimpan`); 
        setShowModal(false); 
        loadData(); 
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menyimpan');
      }
    } catch (err) { 
      toast.error('Gagal menyimpan: ' + err.message); 
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => { 
    setEditingItem(item); 
    setFormData({
      code: item.code || '',
      code_mode: 'manual',
      name: item.name || '',
      group_id: item.group_id || '',
      address: item.address || '',
      city: item.city || '',
      province: item.province || '',
      country: item.country || 'Indonesia',
      postal_code: item.postal_code || '',
      phone: item.phone || '',
      fax: item.fax || '',
      email: item.email || '',
      contact_person: item.contact_person || '',
      birth_date: item.birth_date || '',
      region_id: item.region_id || '',
      sub_region_id: item.sub_region_id || '',
      salesperson_id: item.salesperson_id || '',
      notes: item.notes || '',
      is_active: item.is_active !== false,
      
      can_credit: item.can_credit !== false,
      credit_limit: item.credit_limit || 0,
      credit_days_limit: item.credit_days_limit || 30,
      default_due_days: item.default_due_days || 30,
      max_credit_per_invoice: item.max_credit_per_invoice || 0,
      include_pending_checks: item.include_pending_checks || false,
      default_discount_type: item.default_discount_type || 'none',
      branch_credit_limit: item.branch_credit_limit || 0,
      
      use_tax: item.use_tax !== false,
      tax_type: item.tax_type || 'default',
      tax_value: item.tax_value || 11,
      id_type: item.id_type || 'npwp',
      npwp: item.npwp || '',
      nik: item.nik || '',
      passport: item.passport || '',
      other_doc: item.other_doc || '',
      nitku: item.nitku || '',
      npwp_name: item.npwp_name || '',
      npwp_address: item.npwp_address || '',
      tax_country: item.tax_country || 'Indonesia',
      
      bank_account_no: item.bank_account_no || '',
      bank_account_name: item.bank_account_name || '',
      bank_name: item.bank_name || '',
      default_ar_account: item.default_ar_account || '',
      default_payment_term: item.default_payment_term || 'net30',
      
      points: item.points || 0
    }); 
    setShowModal(true); 
  };
  
  const handleDelete = async (item) => { 
    if (!window.confirm(`Hapus pelanggan "${item.name}"?`)) return; 
    try { 
      await api(`/api/customers/${item.id}`, { method: 'DELETE' }); 
      toast.success('Berhasil dihapus'); 
      loadData(); 
    } catch { 
      toast.error('Gagal menghapus'); 
    } 
  };

  const resetForm = () => {
    setEditingItem(null);
    setFormData({
      code: 'AUTO', code_mode: 'auto', name: '', group_id: '', address: '', city: '',
      province: '', country: 'Indonesia', postal_code: '', phone: '', fax: '', email: '',
      contact_person: '', birth_date: '', region_id: '', sub_region_id: '', salesperson_id: '',
      notes: '', is_active: true,
      can_credit: true, credit_limit: 0, credit_days_limit: 30, default_due_days: 30,
      max_credit_per_invoice: 0, include_pending_checks: false, default_discount_type: 'none',
      branch_credit_limit: 0,
      use_tax: true, tax_type: 'default', tax_value: 11, id_type: 'npwp',
      npwp: '', nik: '', passport: '', other_doc: '', nitku: '', npwp_name: '',
      npwp_address: '', tax_country: 'Indonesia',
      bank_account_no: '', bank_account_name: '', bank_name: '', default_ar_account: '',
      default_payment_term: 'net30', points: 0
    });
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
  };

  return (
    <div className="space-y-4" data-testid="customers-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Daftar Pelanggan</h1>
          <p className="text-gray-400 text-sm">Kelola data pelanggan lengkap dengan kredit dan pajak</p>
        </div>
        <Button onClick={() => { resetForm(); setShowModal(true); }} 
          className="bg-gradient-to-r from-red-600 to-amber-600" data-testid="add-customer-btn">
          <Plus className="h-4 w-4 mr-2" /> Tambah Pelanggan
        </Button>
      </div>

      <Card className="bg-[#1a1214] border-red-900/30">
        <CardContent className="pt-4">
          <div className="flex gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input type="text" placeholder="Cari pelanggan..." value={searchTerm} 
                onChange={(e) => setSearchTerm(e.target.value)} 
                className="pl-10 bg-[#0a0608] border-red-900/30" />
            </div>
            <Button variant="outline" onClick={loadData}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-[#1a1214] border-red-900/30">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-red-900/20">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA PELANGGAN</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TELEPON</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">GRUP</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">KREDIT</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">LIMIT</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">POINT</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/20">
                {loading ? (
                  <tr><td colSpan={9} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
                ) : items.length === 0 ? (
                  <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-400">Belum ada data pelanggan</td></tr>
                ) : items.map(item => (
                  <tr key={item.id} className="hover:bg-red-900/10">
                    <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-200">{item.name}</div>
                      {item.email && <div className="text-xs text-gray-500 flex items-center gap-1"><Mail className="h-3 w-3" />{item.email}</div>}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {item.phone && <div className="flex items-center gap-1"><Phone className="h-3 w-3" /> {item.phone}</div>}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">{item.group_name || '-'}</td>
                    <td className="px-4 py-3 text-center">
                      <Badge variant={item.can_credit !== false ? "default" : "secondary"} className={item.can_credit !== false ? "bg-green-600" : ""}>
                        {item.can_credit !== false ? 'Ya' : 'Tidak'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-300">
                      {formatCurrency(item.credit_limit)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      <span className="flex items-center justify-end gap-1 text-amber-400">
                        <Star className="h-3 w-3" /> {item.points || 0}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge variant={item.is_active !== false ? "default" : "destructive"} className={item.is_active !== false ? "bg-green-600" : ""}>
                        {item.is_active !== false ? 'Aktif' : 'Nonaktif'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <Button size="sm" variant="ghost" onClick={() => handleEdit(item)} className="text-blue-400 hover:text-blue-300">
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => handleDelete(item)} className="text-red-400 hover:text-red-300">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Customer Form Modal */}
      <Dialog open={showModal} onOpenChange={(open) => !open && setShowModal(false)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-[#1a1214] border-red-900/30">
          <DialogHeader>
            <DialogTitle className="text-amber-100 flex items-center gap-2">
              <User className="h-5 w-5" />
              {editingItem ? 'Edit' : 'Tambah'} Pelanggan
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit}>
            <Tabs defaultValue="general" className="w-full">
              <TabsList className="grid w-full grid-cols-4 bg-[#0a0608]">
                <TabsTrigger value="general" className="data-[state=active]:bg-red-900/50">
                  <User className="h-4 w-4 mr-1" /> Umum
                </TabsTrigger>
                <TabsTrigger value="credit" className="data-[state=active]:bg-red-900/50">
                  <CreditCard className="h-4 w-4 mr-1" /> Kredit
                </TabsTrigger>
                <TabsTrigger value="tax" className="data-[state=active]:bg-red-900/50">
                  <FileText className="h-4 w-4 mr-1" /> Pajak
                </TabsTrigger>
                <TabsTrigger value="bank" className="data-[state=active]:bg-red-900/50">
                  <Building className="h-4 w-4 mr-1" /> Bank
                </TabsTrigger>
              </TabsList>

              {/* Tab: Data Umum */}
              <TabsContent value="general" className="space-y-4 mt-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label className="text-gray-300">Mode Kode</Label>
                    <Select value={formData.code === 'AUTO' ? 'auto' : 'manual'}
                      onValueChange={(v) => setFormData({...formData, code: v === 'auto' ? 'AUTO' : '', code_mode: v})}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="auto">AUTO</SelectItem>
                        <SelectItem value="manual">MANUAL</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-gray-300">Kode Pelanggan <span className="text-red-400">*</span></Label>
                    <Input value={formData.code} 
                      onChange={(e) => setFormData({...formData, code: e.target.value.toUpperCase(), code_mode: 'manual'})}
                      disabled={formData.code === 'AUTO'}
                      className={`bg-[#0a0608] border-red-900/30 ${formData.code === 'AUTO' ? 'text-amber-400' : ''}`}
                      placeholder={formData.code === 'AUTO' ? 'Akan digenerate' : 'Masukkan kode'} />
                  </div>
                  <div>
                    <Label className="text-gray-300">Grup Pelanggan</Label>
                    <Select value={formData.group_id || 'none'} onValueChange={(v) => setFormData({...formData, group_id: v === 'none' ? '' : v})}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue placeholder="Pilih grup" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">-- Tidak ada --</SelectItem>
                        {groups.map(g => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300">Nama Pelanggan <span className="text-red-400">*</span></Label>
                    <Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" placeholder="Nama lengkap pelanggan" required />
                  </div>
                  <div>
                    <Label className="text-gray-300">Kontak Person</Label>
                    <Input value={formData.contact_person} onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" placeholder="Nama kontak" />
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label className="text-gray-300">Telepon</Label>
                    <Input value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" placeholder="08xx" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Fax</Label>
                    <Input value={formData.fax} onChange={(e) => setFormData({...formData, fax: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" placeholder="Fax" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Email</Label>
                    <Input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" placeholder="email@domain.com" />
                  </div>
                </div>
                
                <div>
                  <Label className="text-gray-300">Alamat</Label>
                  <Input value={formData.address} onChange={(e) => setFormData({...formData, address: e.target.value})}
                    className="bg-[#0a0608] border-red-900/30" placeholder="Alamat lengkap" />
                </div>
                
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <Label className="text-gray-300">Kota</Label>
                    <Input value={formData.city} onChange={(e) => setFormData({...formData, city: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Provinsi</Label>
                    <Input value={formData.province} onChange={(e) => setFormData({...formData, province: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Negara</Label>
                    <Input value={formData.country} onChange={(e) => setFormData({...formData, country: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Kode Pos</Label>
                    <Input value={formData.postal_code} onChange={(e) => setFormData({...formData, postal_code: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label className="text-gray-300">Wilayah</Label>
                    <Select value={formData.region_id || 'none'} onValueChange={(v) => setFormData({...formData, region_id: v === 'none' ? '' : v})}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue placeholder="Pilih wilayah" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">-- Tidak ada --</SelectItem>
                        {regions.map(r => <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-gray-300">Sales Default</Label>
                    <Select value={formData.salesperson_id || 'none'} onValueChange={(v) => setFormData({...formData, salesperson_id: v === 'none' ? '' : v})}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue placeholder="Pilih sales" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">-- Tidak ada --</SelectItem>
                        {salesPersons.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-gray-300">Tanggal Lahir</Label>
                    <Input type="date" value={formData.birth_date} onChange={(e) => setFormData({...formData, birth_date: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                </div>
                
                <div>
                  <Label className="text-gray-300">Catatan</Label>
                  <Input value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})}
                    className="bg-[#0a0608] border-red-900/30" placeholder="Catatan internal" />
                </div>
                
                <div className="flex items-center gap-2">
                  <Switch checked={formData.is_active} onCheckedChange={(c) => setFormData({...formData, is_active: c})} />
                  <Label className="text-gray-300">Pelanggan Aktif</Label>
                </div>
              </TabsContent>

              {/* Tab: Data Kredit */}
              <TabsContent value="credit" className="space-y-4 mt-4">
                <div className="p-4 bg-amber-900/20 border border-amber-700/30 rounded-lg">
                  <p className="text-amber-300 text-sm">Pengaturan kredit akan divalidasi saat transaksi penjualan kredit</p>
                </div>
                
                <div className="flex items-center gap-4">
                  <Switch checked={formData.can_credit} onCheckedChange={(c) => setFormData({...formData, can_credit: c})} />
                  <Label className="text-gray-300 font-semibold">Bisa Kredit / Piutang</Label>
                </div>
                
                {formData.can_credit && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-gray-300">Limit Jumlah Piutang</Label>
                        <Input type="number" value={formData.credit_limit} 
                          onChange={(e) => setFormData({...formData, credit_limit: parseFloat(e.target.value) || 0})}
                          className="bg-[#0a0608] border-red-900/30" />
                        <p className="text-xs text-gray-500 mt-1">0 = tidak ada limit</p>
                      </div>
                      <div>
                        <Label className="text-gray-300">Limit Hari Piutang</Label>
                        <Input type="number" value={formData.credit_days_limit} 
                          onChange={(e) => setFormData({...formData, credit_days_limit: parseInt(e.target.value) || 30})}
                          className="bg-[#0a0608] border-red-900/30" />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-gray-300">Jatuh Tempo Default (hari)</Label>
                        <Input type="number" value={formData.default_due_days} 
                          onChange={(e) => setFormData({...formData, default_due_days: parseInt(e.target.value) || 30})}
                          className="bg-[#0a0608] border-red-900/30" />
                      </div>
                      <div>
                        <Label className="text-gray-300">Max Kredit per Nota</Label>
                        <Input type="number" value={formData.max_credit_per_invoice} 
                          onChange={(e) => setFormData({...formData, max_credit_per_invoice: parseFloat(e.target.value) || 0})}
                          className="bg-[#0a0608] border-red-900/30" />
                        <p className="text-xs text-gray-500 mt-1">0 = tidak ada limit</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <Switch checked={formData.include_pending_checks} 
                        onCheckedChange={(c) => setFormData({...formData, include_pending_checks: c})} />
                      <Label className="text-gray-300">Include Cek/BG Belum Lunas dalam Perhitungan</Label>
                    </div>
                    
                    <div>
                      <Label className="text-gray-300">Default Tipe Potongan</Label>
                      <Select value={formData.default_discount_type} 
                        onValueChange={(v) => setFormData({...formData, default_discount_type: v})}>
                        <SelectTrigger className="bg-[#0a0608] border-red-900/30 max-w-xs"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Tidak ada</SelectItem>
                          <SelectItem value="percent">Persentase</SelectItem>
                          <SelectItem value="nominal">Nominal</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                )}
              </TabsContent>

              {/* Tab: Data Pajak */}
              <TabsContent value="tax" className="space-y-4 mt-4">
                <div className="flex items-center gap-4">
                  <Switch checked={formData.use_tax} onCheckedChange={(c) => setFormData({...formData, use_tax: c})} />
                  <Label className="text-gray-300 font-semibold">Menggunakan Pajak</Label>
                </div>
                
                {formData.use_tax && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-gray-300">Jenis Pajak</Label>
                        <Select value={formData.tax_type} onValueChange={(v) => setFormData({...formData, tax_type: v})}>
                          <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="default">Default (PPN 11%)</SelectItem>
                            <SelectItem value="custom">Custom</SelectItem>
                            <SelectItem value="exempt">Bebas Pajak</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      {formData.tax_type === 'custom' && (
                        <div>
                          <Label className="text-gray-300">Nilai Pajak (%)</Label>
                          <Input type="number" value={formData.tax_value} 
                            onChange={(e) => setFormData({...formData, tax_value: parseFloat(e.target.value) || 0})}
                            className="bg-[#0a0608] border-red-900/30" />
                        </div>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-gray-300">Jenis Dokumen</Label>
                        <Select value={formData.id_type} onValueChange={(v) => setFormData({...formData, id_type: v})}>
                          <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="npwp">NPWP</SelectItem>
                            <SelectItem value="nik">NIK</SelectItem>
                            <SelectItem value="passport">Paspor</SelectItem>
                            <SelectItem value="other">Dokumen Lain</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-gray-300">
                          {formData.id_type === 'npwp' ? 'NPWP' : formData.id_type === 'nik' ? 'NIK' : formData.id_type === 'passport' ? 'No. Paspor' : 'No. Dokumen'}
                        </Label>
                        <Input value={formData.id_type === 'npwp' ? formData.npwp : formData.id_type === 'nik' ? formData.nik : formData.id_type === 'passport' ? formData.passport : formData.other_doc}
                          onChange={(e) => {
                            const field = formData.id_type === 'npwp' ? 'npwp' : formData.id_type === 'nik' ? 'nik' : formData.id_type === 'passport' ? 'passport' : 'other_doc';
                            setFormData({...formData, [field]: e.target.value});
                          }}
                          className="bg-[#0a0608] border-red-900/30" />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-gray-300">NITKU</Label>
                        <Input value={formData.nitku} onChange={(e) => setFormData({...formData, nitku: e.target.value})}
                          className="bg-[#0a0608] border-red-900/30" />
                      </div>
                      <div>
                        <Label className="text-gray-300">Nama NPWP</Label>
                        <Input value={formData.npwp_name} onChange={(e) => setFormData({...formData, npwp_name: e.target.value})}
                          className="bg-[#0a0608] border-red-900/30" />
                      </div>
                    </div>
                    
                    <div>
                      <Label className="text-gray-300">Alamat NPWP</Label>
                      <Input value={formData.npwp_address} onChange={(e) => setFormData({...formData, npwp_address: e.target.value})}
                        className="bg-[#0a0608] border-red-900/30" />
                    </div>
                  </>
                )}
              </TabsContent>

              {/* Tab: Data Bank */}
              <TabsContent value="bank" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300">Nama Bank</Label>
                    <Input value={formData.bank_name} onChange={(e) => setFormData({...formData, bank_name: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" placeholder="BCA, Mandiri, BNI, dll" />
                  </div>
                  <div>
                    <Label className="text-gray-300">No. Rekening</Label>
                    <Input value={formData.bank_account_no} onChange={(e) => setFormData({...formData, bank_account_no: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                </div>
                
                <div>
                  <Label className="text-gray-300">Nama Rekening (a.n.)</Label>
                  <Input value={formData.bank_account_name} onChange={(e) => setFormData({...formData, bank_account_name: e.target.value})}
                    className="bg-[#0a0608] border-red-900/30" />
                </div>
                
                <div>
                  <Label className="text-gray-300">Termin Pembayaran Default</Label>
                  <Select value={formData.default_payment_term} onValueChange={(v) => setFormData({...formData, default_payment_term: v})}>
                    <SelectTrigger className="bg-[#0a0608] border-red-900/30 max-w-xs"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cod">COD (Cash on Delivery)</SelectItem>
                      <SelectItem value="net7">Net 7</SelectItem>
                      <SelectItem value="net14">Net 14</SelectItem>
                      <SelectItem value="net30">Net 30</SelectItem>
                      <SelectItem value="net45">Net 45</SelectItem>
                      <SelectItem value="net60">Net 60</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </TabsContent>
            </Tabs>

            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setShowModal(false)} disabled={saving}>
                Batal
              </Button>
              <Button type="submit" className="bg-gradient-to-r from-red-600 to-amber-600" disabled={saving} data-testid="save-customer-btn">
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Simpan
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MasterCustomersAdvanced;
