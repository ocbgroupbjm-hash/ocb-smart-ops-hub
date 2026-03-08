import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Edit, Phone, Mail, MapPin, Loader2, X, Save, Users, Star, Gift } from 'lucide-react';
import { toast } from 'sonner';

const Customers = () => {
  const { api } = useAuth();
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [segment, setSegment] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ name: '', phone: '', email: '', address: '', city: '', segment: 'regular', notes: '' });

  useEffect(() => { loadCustomers(); }, [search, segment]);

  const loadCustomers = async () => {
    setLoading(true);
    try {
      let url = `/api/customers?limit=100`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (segment) url += `&segment=${segment}`;
      const res = await api(url);
      if (res.ok) { const data = await res.json(); setCustomers(data.items || []); }
    } catch (err) { toast.error('Gagal memuat data pelanggan'); }
    finally { setLoading(false); }
  };

  const openModal = (customer = null) => {
    if (customer) { setEditingCustomer(customer); setForm({ ...customer }); }
    else { setEditingCustomer(null); setForm({ name: '', phone: '', email: '', address: '', city: '', segment: 'regular', notes: '' }); }
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.phone) { toast.error('Nama dan nomor HP wajib diisi'); return; }
    setSaving(true);
    try {
      const url = editingCustomer ? `/api/customers/${editingCustomer.id}` : '/api/customers';
      const method = editingCustomer ? 'PUT' : 'POST';
      const res = await api(url, { method, body: JSON.stringify(form) });
      if (res.ok) {
        toast.success(editingCustomer ? 'Pelanggan diperbarui' : 'Pelanggan ditambahkan');
        setShowModal(false);
        loadCustomers();
      } else { const error = await res.json(); toast.error(error.detail || 'Gagal menyimpan'); }
    } catch (err) { toast.error('Gagal menyimpan'); }
    finally { setSaving(false); }
  };

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  const segments = [
    { value: 'regular', label: 'Reguler' },
    { value: 'member', label: 'Member' },
    { value: 'vip', label: 'VIP' },
    { value: 'reseller', label: 'Reseller' },
    { value: 'wholesale', label: 'Grosir' }
  ];

  const segmentColors = {
    regular: 'bg-gray-900/30 text-gray-400',
    member: 'bg-blue-900/30 text-blue-400',
    vip: 'bg-amber-900/30 text-amber-400',
    reseller: 'bg-purple-900/30 text-purple-400',
    wholesale: 'bg-green-900/30 text-green-400'
  };

  const segmentLabels = {
    regular: 'Reguler', member: 'Member', vip: 'VIP', reseller: 'Reseller', wholesale: 'Grosir'
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Pelanggan</h1>
          <p className="text-gray-400">Kelola database pelanggan</p>
        </div>
        <button onClick={() => openModal()} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2" data-testid="add-customer-btn">
          <Plus className="h-5 w-5" /> Tambah Pelanggan
        </button>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input type="text" placeholder="Cari nama atau nomor HP..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-10 pr-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg" />
        </div>
        <select value={segment} onChange={(e) => setSegment(e.target.value)} className="px-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg">
          <option value="">Semua Segmen</option>
          {segments.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-red-400" />
          </div>
        ) : customers.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-400">
            <Users className="h-16 w-16 mx-auto mb-4 opacity-30" />
            <p>Tidak ada pelanggan</p>
          </div>
        ) : (
          customers.map(customer => (
            <div key={customer.id} className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 hover:border-red-700/50 transition-colors" data-testid={`customer-card-${customer.id}`}>
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-semibold text-lg">{customer.name}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded ${segmentColors[customer.segment]}`}>
                    {segmentLabels[customer.segment] || customer.segment}
                  </span>
                </div>
                <button onClick={() => openModal(customer)} className="p-2 text-blue-400 hover:bg-blue-900/20 rounded">
                  <Edit className="h-4 w-4" />
                </button>
              </div>
              
              <div className="space-y-2 text-sm text-gray-400">
                <div className="flex items-center gap-2"><Phone className="h-4 w-4" />{customer.phone}</div>
                {customer.email && <div className="flex items-center gap-2"><Mail className="h-4 w-4" />{customer.email}</div>}
                {customer.city && <div className="flex items-center gap-2"><MapPin className="h-4 w-4" />{customer.city}</div>}
              </div>

              <div className="mt-4 pt-3 border-t border-red-900/30 grid grid-cols-3 gap-2 text-sm">
                <div>
                  <div className="text-gray-400">Transaksi</div>
                  <div className="font-semibold">{customer.total_transactions || 0}</div>
                </div>
                <div>
                  <div className="text-gray-400">Total Belanja</div>
                  <div className="font-semibold text-amber-400">{formatRupiah(customer.total_spent)}</div>
                </div>
                <div>
                  <div className="text-gray-400 flex items-center gap-1"><Gift className="h-3 w-3" />Poin</div>
                  <div className="font-semibold text-green-400">{customer.loyalty_points || 0}</div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <h2 className="text-xl font-bold">{editingCustomer ? 'Edit Pelanggan' : 'Tambah Pelanggan'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama *</label>
                <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nomor HP *</label>
                <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Email</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Segmen</label>
                <select value={form.segment} onChange={(e) => setForm({ ...form, segment: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                  {segments.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Kota</label>
                <input type="text" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Alamat</label>
                <textarea value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
              </div>
              
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button type="submit" disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50 flex items-center justify-center gap-2">
                  {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5" />}
                  {saving ? 'Menyimpan...' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Customers;
