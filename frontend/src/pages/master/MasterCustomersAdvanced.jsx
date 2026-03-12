import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Switch } from '../../components/ui/switch';
import { Textarea } from '../../components/ui/textarea';
import { toast } from 'sonner';
import { 
  Plus, Search, Edit, Trash2, Save, X, Users, FileText, 
  CreditCard, Building2, Phone, Mail, MapPin, Calendar,
  DollarSign, Shield, RefreshCw, ChevronLeft
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MasterCustomersAdvanced = () => {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGroup, setSelectedGroup] = useState('');
  const [customerGroups, setCustomerGroups] = useState([]);
  const [salesList, setSalesList] = useState([]);
  
  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [activeTab, setActiveTab] = useState('general');
  
  // Form data
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    customer_group: 'umum',
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
    region: '',
    sub_region: '',
    default_sales_id: '',
    default_sales_name: '',
    notes: '',
    is_active: true,
    tax_info: {
      tax_type: 'default',
      tax_document_type: 'npwp',
      npwp: '',
      nik: '',
      passport: '',
      other_document: '',
      nitku: '',
      npwp_name: '',
      npwp_address: '',
      tax_country: 'ID'
    },
    credit_info: {
      can_credit: false,
      credit_limit: 0,
      credit_days_limit: 30,
      default_due_days: 30,
      max_invoice_amount: 0,
      include_outstanding_check: true,
      default_discount_type: '',
      grace_period_days: 0
    },
    accounting_info: {
      ar_account_code: '1-1300',
      ar_account_name: 'Piutang Usaha',
      default_payment_term: '',
      default_payment_method: ''
    }
  });

  const fetchCustomers = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedGroup && selectedGroup !== 'all') params.append('customer_group', selectedGroup);
      
      const res = await fetch(`${API_URL}/api/master-advanced/customers?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setCustomers(data.items || []);
    } catch (err) {
      console.error('Error fetching customers:', err);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, selectedGroup]);

  const fetchCustomerGroups = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/master-advanced/customer-groups`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setCustomerGroups(data.items || []);
    } catch (err) {
      console.error('Error fetching groups:', err);
    }
  };

  const fetchSalesList = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/users?role=sales`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setSalesList(Array.isArray(data) ? data : data.items || []);
    } catch (err) {
      console.error('Error fetching sales:', err);
    }
  };

  useEffect(() => {
    fetchCustomers();
    fetchCustomerGroups();
    fetchSalesList();
  }, [fetchCustomers]);

  const handleInputChange = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
  };

  const resetForm = () => {
    setFormData({
      code: '',
      name: '',
      customer_group: 'umum',
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
      region: '',
      sub_region: '',
      default_sales_id: '',
      default_sales_name: '',
      notes: '',
      is_active: true,
      tax_info: {
        tax_type: 'default',
        tax_document_type: 'npwp',
        npwp: '',
        nik: '',
        passport: '',
        other_document: '',
        nitku: '',
        npwp_name: '',
        npwp_address: '',
        tax_country: 'ID'
      },
      credit_info: {
        can_credit: false,
        credit_limit: 0,
        credit_days_limit: 30,
        default_due_days: 30,
        max_invoice_amount: 0,
        include_outstanding_check: true,
        default_discount_type: '',
        grace_period_days: 0
      },
      accounting_info: {
        ar_account_code: '1-1300',
        ar_account_name: 'Piutang Usaha',
        default_payment_term: '',
        default_payment_method: ''
      }
    });
    setEditingCustomer(null);
    setActiveTab('general');
  };

  const openNewForm = () => {
    resetForm();
    setShowForm(true);
  };

  const openEditForm = async (customer) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/master-advanced/customers/${customer.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      
      setFormData({
        code: data.code || '',
        name: data.name || '',
        customer_group: data.customer_group || 'umum',
        address: data.address || '',
        city: data.city || '',
        province: data.province || '',
        country: data.country || 'Indonesia',
        postal_code: data.postal_code || '',
        phone: data.phone || '',
        fax: data.fax || '',
        email: data.email || '',
        contact_person: data.contact_person || '',
        birth_date: data.birth_date || '',
        region: data.region || '',
        sub_region: data.sub_region || '',
        default_sales_id: data.default_sales_id || '',
        default_sales_name: data.default_sales_name || '',
        notes: data.notes || '',
        is_active: data.is_active !== false,
        tax_info: data.tax_info || formData.tax_info,
        credit_info: data.credit_info || formData.credit_info,
        accounting_info: data.accounting_info || formData.accounting_info
      });
      setEditingCustomer(data);
      setShowForm(true);
    } catch (err) {
      toast.error('Gagal memuat data customer');
    }
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      toast.error('Nama customer wajib diisi');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const url = editingCustomer 
        ? `${API_URL}/api/master-advanced/customers/${editingCustomer.id}`
        : `${API_URL}/api/master-advanced/customers`;
      
      const res = await fetch(url, {
        method: editingCustomer ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const data = await res.json();
      
      if (res.ok && data.success) {
        toast.success(editingCustomer ? 'Customer berhasil diupdate' : 'Customer berhasil dibuat');
        setShowForm(false);
        resetForm();
        fetchCustomers();
      } else {
        toast.error(data.detail || 'Gagal menyimpan customer');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
  };

  // Render Form
  if (showForm) {
    return (
      <div className="p-4 space-y-4" data-testid="customer-advanced-form">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => { setShowForm(false); resetForm(); }}>
            <ChevronLeft className="h-4 w-4 mr-1" />
            Kembali
          </Button>
          <h1 className="text-xl font-bold">
            {editingCustomer ? 'Edit Customer' : 'Tambah Customer Baru'}
          </h1>
        </div>

        <Card>
          <CardContent className="p-4">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-4 mb-4">
                <TabsTrigger value="general" className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  Data Umum
                </TabsTrigger>
                <TabsTrigger value="tax" className="flex items-center gap-1">
                  <FileText className="h-4 w-4" />
                  Pajak
                </TabsTrigger>
                <TabsTrigger value="credit" className="flex items-center gap-1">
                  <CreditCard className="h-4 w-4" />
                  Kredit/Piutang
                </TabsTrigger>
                <TabsTrigger value="accounting" className="flex items-center gap-1">
                  <DollarSign className="h-4 w-4" />
                  Akuntansi
                </TabsTrigger>
              </TabsList>

              {/* Tab: Data Umum */}
              <TabsContent value="general" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label>Kode Customer</Label>
                    <Input
                      value={formData.code}
                      onChange={(e) => handleInputChange('code', e.target.value)}
                      placeholder="Auto jika kosong"
                      data-testid="customer-code-input"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Label>Nama Customer *</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="Nama lengkap customer"
                      data-testid="customer-name-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label>Grup Customer</Label>
                    <Select value={formData.customer_group} onValueChange={(v) => handleInputChange('customer_group', v)}>
                      <SelectTrigger data-testid="customer-group-select">
                        <SelectValue placeholder="Pilih grup" />
                      </SelectTrigger>
                      <SelectContent>
                        {customerGroups.map(g => (
                          <SelectItem key={g.id} value={g.id || g.code}>{g.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Telepon</Label>
                    <Input
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      placeholder="08xx"
                      data-testid="customer-phone-input"
                    />
                  </div>
                  <div>
                    <Label>Fax</Label>
                    <Input
                      value={formData.fax}
                      onChange={(e) => handleInputChange('fax', e.target.value)}
                      placeholder="Fax"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      placeholder="email@example.com"
                      data-testid="customer-email-input"
                    />
                  </div>
                  <div>
                    <Label>Contact Person</Label>
                    <Input
                      value={formData.contact_person}
                      onChange={(e) => handleInputChange('contact_person', e.target.value)}
                      placeholder="Nama kontak"
                    />
                  </div>
                </div>

                <div>
                  <Label>Alamat</Label>
                  <Textarea
                    value={formData.address}
                    onChange={(e) => handleInputChange('address', e.target.value)}
                    placeholder="Alamat lengkap"
                    rows={2}
                    data-testid="customer-address-input"
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <Label>Kota</Label>
                    <Input
                      value={formData.city}
                      onChange={(e) => handleInputChange('city', e.target.value)}
                      placeholder="Kota"
                    />
                  </div>
                  <div>
                    <Label>Provinsi</Label>
                    <Input
                      value={formData.province}
                      onChange={(e) => handleInputChange('province', e.target.value)}
                      placeholder="Provinsi"
                    />
                  </div>
                  <div>
                    <Label>Negara</Label>
                    <Input
                      value={formData.country}
                      onChange={(e) => handleInputChange('country', e.target.value)}
                      placeholder="Negara"
                    />
                  </div>
                  <div>
                    <Label>Kode Pos</Label>
                    <Input
                      value={formData.postal_code}
                      onChange={(e) => handleInputChange('postal_code', e.target.value)}
                      placeholder="12345"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <Label>Wilayah</Label>
                    <Input
                      value={formData.region}
                      onChange={(e) => handleInputChange('region', e.target.value)}
                      placeholder="Wilayah"
                    />
                  </div>
                  <div>
                    <Label>Sub Wilayah</Label>
                    <Input
                      value={formData.sub_region}
                      onChange={(e) => handleInputChange('sub_region', e.target.value)}
                      placeholder="Sub wilayah"
                    />
                  </div>
                  <div>
                    <Label>Tanggal Lahir</Label>
                    <Input
                      type="date"
                      value={formData.birth_date}
                      onChange={(e) => handleInputChange('birth_date', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>Sales Default</Label>
                    <Select value={formData.default_sales_id} onValueChange={(v) => {
                      const sales = salesList.find(s => s.user_id === v);
                      handleInputChange('default_sales_id', v);
                      handleInputChange('default_sales_name', sales?.name || '');
                    }}>
                      <SelectTrigger>
                        <SelectValue placeholder="Pilih sales" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">-- Tidak Ada --</SelectItem>
                        {salesList.map(s => (
                          <SelectItem key={s.user_id} value={s.user_id}>{s.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label>Catatan</Label>
                  <Textarea
                    value={formData.notes}
                    onChange={(e) => handleInputChange('notes', e.target.value)}
                    placeholder="Catatan tambahan"
                    rows={2}
                  />
                </div>

                <div className="flex items-center gap-2">
                  <Switch
                    checked={formData.is_active}
                    onCheckedChange={(v) => handleInputChange('is_active', v)}
                    data-testid="customer-active-switch"
                  />
                  <Label>Aktif</Label>
                </div>
              </TabsContent>

              {/* Tab: Pajak */}
              <TabsContent value="tax" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Tipe Pajak</Label>
                    <Select 
                      value={formData.tax_info.tax_type} 
                      onValueChange={(v) => handleInputChange('tax_info.tax_type', v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="default">Default (Ikut Setting)</SelectItem>
                        <SelectItem value="custom">Custom</SelectItem>
                        <SelectItem value="exempt">Bebas Pajak</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Jenis Dokumen</Label>
                    <Select 
                      value={formData.tax_info.tax_document_type} 
                      onValueChange={(v) => handleInputChange('tax_info.tax_document_type', v)}
                    >
                      <SelectTrigger data-testid="tax-document-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="npwp">NPWP</SelectItem>
                        <SelectItem value="nik">NIK</SelectItem>
                        <SelectItem value="passport">Paspor</SelectItem>
                        <SelectItem value="other">Dokumen Lain</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>NPWP</Label>
                    <Input
                      value={formData.tax_info.npwp}
                      onChange={(e) => handleInputChange('tax_info.npwp', e.target.value)}
                      placeholder="XX.XXX.XXX.X-XXX.XXX"
                      data-testid="npwp-input"
                    />
                  </div>
                  <div>
                    <Label>NIK</Label>
                    <Input
                      value={formData.tax_info.nik}
                      onChange={(e) => handleInputChange('tax_info.nik', e.target.value)}
                      placeholder="16 digit"
                      data-testid="nik-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Paspor</Label>
                    <Input
                      value={formData.tax_info.passport}
                      onChange={(e) => handleInputChange('tax_info.passport', e.target.value)}
                      placeholder="Nomor paspor"
                    />
                  </div>
                  <div>
                    <Label>Dokumen Lain</Label>
                    <Input
                      value={formData.tax_info.other_document}
                      onChange={(e) => handleInputChange('tax_info.other_document', e.target.value)}
                      placeholder="Nomor dokumen lain"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>NITKU</Label>
                    <Input
                      value={formData.tax_info.nitku}
                      onChange={(e) => handleInputChange('tax_info.nitku', e.target.value)}
                      placeholder="Nomor NITKU"
                    />
                  </div>
                  <div>
                    <Label>Negara Referensi Pajak</Label>
                    <Input
                      value={formData.tax_info.tax_country}
                      onChange={(e) => handleInputChange('tax_info.tax_country', e.target.value)}
                      placeholder="ID"
                    />
                  </div>
                </div>

                <div>
                  <Label>Nama NPWP</Label>
                  <Input
                    value={formData.tax_info.npwp_name}
                    onChange={(e) => handleInputChange('tax_info.npwp_name', e.target.value)}
                    placeholder="Nama sesuai NPWP"
                  />
                </div>

                <div>
                  <Label>Alamat NPWP</Label>
                  <Textarea
                    value={formData.tax_info.npwp_address}
                    onChange={(e) => handleInputChange('tax_info.npwp_address', e.target.value)}
                    placeholder="Alamat sesuai NPWP"
                    rows={2}
                  />
                </div>
              </TabsContent>

              {/* Tab: Kredit/Piutang */}
              <TabsContent value="credit" className="space-y-4">
                <div className="flex items-center gap-4 p-4 bg-blue-50 rounded-lg">
                  <Switch
                    checked={formData.credit_info.can_credit}
                    onCheckedChange={(v) => handleInputChange('credit_info.can_credit', v)}
                    data-testid="can-credit-switch"
                  />
                  <div>
                    <Label className="text-base font-semibold">Izinkan Kredit</Label>
                    <p className="text-sm text-gray-500">Customer ini dapat melakukan pembelian kredit</p>
                  </div>
                </div>

                {formData.credit_info.can_credit && (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label>Limit Jumlah Piutang (Rp)</Label>
                        <Input
                          type="number"
                          value={formData.credit_info.credit_limit}
                          onChange={(e) => handleInputChange('credit_info.credit_limit', parseFloat(e.target.value) || 0)}
                          placeholder="0 = tanpa limit"
                          data-testid="credit-limit-input"
                        />
                        <p className="text-xs text-gray-500 mt-1">0 = tanpa batas limit</p>
                      </div>
                      <div>
                        <Label>Limit Hari Piutang</Label>
                        <Input
                          type="number"
                          value={formData.credit_info.credit_days_limit}
                          onChange={(e) => handleInputChange('credit_info.credit_days_limit', parseInt(e.target.value) || 30)}
                          placeholder="30"
                          data-testid="credit-days-input"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label>Jatuh Tempo Default (hari)</Label>
                        <Input
                          type="number"
                          value={formData.credit_info.default_due_days}
                          onChange={(e) => handleInputChange('credit_info.default_due_days', parseInt(e.target.value) || 30)}
                          placeholder="30"
                          data-testid="due-days-input"
                        />
                      </div>
                      <div>
                        <Label>Max Nominal Kredit Per Nota (Rp)</Label>
                        <Input
                          type="number"
                          value={formData.credit_info.max_invoice_amount}
                          onChange={(e) => handleInputChange('credit_info.max_invoice_amount', parseFloat(e.target.value) || 0)}
                          placeholder="0 = tanpa limit"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label>Grace Period (hari)</Label>
                        <Input
                          type="number"
                          value={formData.credit_info.grace_period_days}
                          onChange={(e) => handleInputChange('credit_info.grace_period_days', parseInt(e.target.value) || 0)}
                          placeholder="0"
                        />
                      </div>
                      <div>
                        <Label>Tipe Potongan Default</Label>
                        <Select 
                          value={formData.credit_info.default_discount_type} 
                          onValueChange={(v) => handleInputChange('credit_info.default_discount_type', v)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Pilih tipe" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="none">-- Tidak Ada --</SelectItem>
                            <SelectItem value="percentage">Persentase</SelectItem>
                            <SelectItem value="nominal">Nominal</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Switch
                        checked={formData.credit_info.include_outstanding_check}
                        onCheckedChange={(v) => handleInputChange('credit_info.include_outstanding_check', v)}
                      />
                      <Label>Include Cek/BG Belum Lunas dalam Perhitungan Limit</Label>
                    </div>
                  </>
                )}
              </TabsContent>

              {/* Tab: Akuntansi */}
              <TabsContent value="accounting" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Akun AR Default</Label>
                    <Input
                      value={formData.accounting_info.ar_account_code}
                      onChange={(e) => handleInputChange('accounting_info.ar_account_code', e.target.value)}
                      placeholder="1-1300"
                    />
                  </div>
                  <div>
                    <Label>Nama Akun AR</Label>
                    <Input
                      value={formData.accounting_info.ar_account_name}
                      onChange={(e) => handleInputChange('accounting_info.ar_account_name', e.target.value)}
                      placeholder="Piutang Usaha"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Termin Pembayaran Default</Label>
                    <Select 
                      value={formData.accounting_info.default_payment_term} 
                      onValueChange={(v) => handleInputChange('accounting_info.default_payment_term', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Pilih termin" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">-- Tidak Ada --</SelectItem>
                        <SelectItem value="cod">COD</SelectItem>
                        <SelectItem value="net7">Net 7</SelectItem>
                        <SelectItem value="net14">Net 14</SelectItem>
                        <SelectItem value="net30">Net 30</SelectItem>
                        <SelectItem value="net60">Net 60</SelectItem>
                        <SelectItem value="net90">Net 90</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Metode Pembayaran Default</Label>
                    <Select 
                      value={formData.accounting_info.default_payment_method} 
                      onValueChange={(v) => handleInputChange('accounting_info.default_payment_method', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Pilih metode" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">-- Tidak Ada --</SelectItem>
                        <SelectItem value="cash">Tunai</SelectItem>
                        <SelectItem value="transfer">Transfer Bank</SelectItem>
                        <SelectItem value="giro">Giro</SelectItem>
                        <SelectItem value="cek">Cek</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            <div className="flex justify-end gap-2 mt-6 pt-4 border-t">
              <Button variant="outline" onClick={() => { setShowForm(false); resetForm(); }}>
                <X className="h-4 w-4 mr-1" />
                Batal
              </Button>
              <Button onClick={handleSubmit} data-testid="save-customer-btn">
                <Save className="h-4 w-4 mr-1" />
                {editingCustomer ? 'Update' : 'Simpan'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Render List
  return (
    <div className="p-4 space-y-4" data-testid="customer-advanced-list">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="h-6 w-6" />
            Master Customer Advanced
          </h1>
          <p className="text-gray-500">Kelola data pelanggan dengan informasi lengkap</p>
        </div>
        <Button onClick={openNewForm} data-testid="add-customer-btn">
          <Plus className="h-4 w-4 mr-1" />
          Tambah Customer
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Cari nama, kode, telepon, email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                  data-testid="search-customer-input"
                />
              </div>
            </div>
            <Select value={selectedGroup} onValueChange={setSelectedGroup}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Semua Grup" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua Grup</SelectItem>
                {customerGroups.map(g => (
                  <SelectItem key={g.id} value={g.id || g.code}>{g.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={fetchCustomers}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Customer List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : customers.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Belum ada data customer
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kode</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nama</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grup</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Telepon</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kota</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kredit</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Limit</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {customers.map((customer) => (
                    <tr key={customer.id} className="hover:bg-gray-50" data-testid={`customer-row-${customer.id}`}>
                      <td className="px-4 py-3 text-sm font-medium">{customer.code}</td>
                      <td className="px-4 py-3">
                        <div>
                          <div className="font-medium">{customer.name}</div>
                          {customer.email && (
                            <div className="text-xs text-gray-500">{customer.email}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{customer.customer_group || 'Umum'}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm">{customer.phone || '-'}</td>
                      <td className="px-4 py-3 text-sm">{customer.city || '-'}</td>
                      <td className="px-4 py-3">
                        {customer.credit_info?.can_credit ? (
                          <Badge className="bg-green-100 text-green-800">Ya</Badge>
                        ) : (
                          <Badge variant="outline">Tidak</Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {customer.credit_info?.credit_limit > 0 
                          ? formatCurrency(customer.credit_info.credit_limit)
                          : '-'}
                      </td>
                      <td className="px-4 py-3">
                        {customer.is_active !== false ? (
                          <Badge className="bg-green-100 text-green-800">Aktif</Badge>
                        ) : (
                          <Badge variant="destructive">Nonaktif</Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <Button 
                          size="sm" 
                          variant="ghost" 
                          onClick={() => openEditForm(customer)}
                          data-testid={`edit-customer-${customer.id}`}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default MasterCustomersAdvanced;
