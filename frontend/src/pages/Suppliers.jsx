import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Edit, Warehouse, Phone, Mail, CreditCard, X, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const Suppliers = () => {
  const { api } = useAuth();
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    code: '', name: '', contact_person: '', phone: '', email: '', address: '', city: '',
    payment_terms: 30, bank_name: '', bank_account: '', bank_holder: '', notes: ''
  });

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  useEffect(() => { loadSuppliers(); }, [search]);

  const loadSuppliers = async () => {
    setLoading(true);
    try {
      let url = `/api/suppliers?limit=100`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      const res = await api(url);
      if (res.ok) { const data = await res.json(); setSuppliers(data.items || []); }
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  };

  const openModal = (supplier = null) => {
    if (supplier) { setEditingSupplier(supplier); setForm({ ...supplier }); }
    else {
      setEditingSupplier(null);
      setForm({ code: '', name: '', contact_person: '', phone: '', email: '', address: '', city: '', payment_terms: 30, bank_name: '', bank_account: '', bank_holder: '', notes: '' });
    }
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.code || !form.name) { toast.error('Kode dan nama wajib diisi'); return; }
    setSaving(true);
    try {
      const url = editingSupplier ? `/api/suppliers/${editingSupplier.id}` : '/api/suppliers';
      const method = editingSupplier ? 'PUT' : 'POST';
      const res = await api(url, { method, body: JSON.stringify(form) });
      if (res.ok) { toast.success(editingSupplier ? 'Supplier diperbarui' : 'Supplier ditambahkan'); setShowModal(false); loadSuppliers(); }
      else { const error = await res.json(); toast.error(error.detail || 'Gagal'); }
    } catch (err) { toast.error('Gagal'); }
    finally { setSaving(false); }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Supplier</h1>
          <p className="text-gray-400">Kelola data supplier dan rekanan</p>
        </div>
        <button onClick={() => openModal()} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-5 w-5" /> Tambah Supplier
        </button>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input type="text" placeholder="Cari supplier..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-10 pr-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-red-400" /></div>
        ) : suppliers.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-400"><Warehouse className="h-16 w-16 mx-auto mb-4 opacity-30" /><p>Belum ada supplier</p></div>
        ) : (
          suppliers.map(supplier => (
            <div key={supplier.id} className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5 hover:border-red-700/50 transition-colors">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-semibold text-lg">{supplier.name}</h3>
                  <span className="text-sm text-gray-400">{supplier.code}</span>
                </div>
                <button onClick={() => openModal(supplier)} className="p-2 text-blue-400 hover:bg-blue-900/20 rounded"><Edit className="h-4 w-4" /></button>
              </div>
              
              <div className="space-y-2 text-sm text-gray-400">
                {supplier.contact_person && <div className="font-medium text-gray-300">PIC: {supplier.contact_person}</div>}
                {supplier.phone && <div className="flex items-center gap-2"><Phone className="h-4 w-4" />{supplier.phone}</div>}
                {supplier.email && <div className="flex items-center gap-2"><Mail className="h-4 w-4" />{supplier.email}</div>}
                {supplier.bank_name && <div className="flex items-center gap-2"><CreditCard className="h-4 w-4" />{supplier.bank_name} - {supplier.bank_account}</div>}
              </div>

              <div className="mt-4 pt-3 border-t border-red-900/30 flex justify-between items-center">
                <div>
                  <div className="text-xs text-gray-400">Hutang</div>
                  <div className={`font-semibold ${supplier.debt_balance > 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {formatRupiah(supplier.debt_balance)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-400">Tempo</div>
                  <div className="font-semibold">{supplier.payment_terms} hari</div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center sticky top-0 bg-[#1a1214]">
              <h2 className="text-xl font-bold">{editingSupplier ? 'Edit Supplier' : 'Tambah Supplier'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kode Supplier *</label>
                  <input type="text" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required disabled={!!editingSupplier} />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nama Supplier *</label>
                  <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nama Kontak (PIC)</label>
                  <input type="text" value={form.contact_person} onChange={(e) => setForm({ ...form, contact_person: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Telepon</label>
                  <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Email</label>
                  <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kota</label>
                  <input type="text" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Alamat</label>
                <textarea value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
              </div>

              <div className="border-t border-red-900/30 pt-4">
                <h3 className="text-lg font-semibold mb-3 text-amber-100">Informasi Bank</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Nama Bank</label>
                    <input type="text" value={form.bank_name} onChange={(e) => setForm({ ...form, bank_name: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">No. Rekening</label>
                    <input type="text" value={form.bank_account} onChange={(e) => setForm({ ...form, bank_account: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Atas Nama</label>
                    <input type="text" value={form.bank_holder} onChange={(e) => setForm({ ...form, bank_holder: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Tempo Pembayaran (Hari)</label>
                <input type="number" value={form.payment_terms} onChange={(e) => setForm({ ...form, payment_terms: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
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

export default Suppliers;
