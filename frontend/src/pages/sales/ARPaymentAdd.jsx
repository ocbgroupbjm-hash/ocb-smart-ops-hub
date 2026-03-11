import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Save, X, Loader2, Wallet, Trash2, Plus
} from 'lucide-react';
import { toast } from 'sonner';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';

const ARPaymentAdd = () => {
  const { api, user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [customers, setCustomers] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [receivables, setReceivables] = useState([]);

  const [form, setForm] = useState({
    payment_number: '',
    date: new Date().toISOString().split('T')[0],
    customer_id: '',
    account_id: '',
    payment_method: 'cash',
    reference_no: '',
    notes: '',
    items: [],
    total_discount: 0,
    total_payment: 0,
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        const [custRes, accRes] = await Promise.all([
          api('/api/customers'),
          api('/api/accounting/coa?type=kas')
        ]);
        
        if (custRes.ok) setCustomers((await custRes.json()).items || []);
        if (accRes.ok) setAccounts((await accRes.json()).accounts || []);
        
        const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        const seq = String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0');
        setForm(prev => ({ ...prev, payment_number: `ARP-${dateStr}-${seq}` }));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [api]);

  const loadReceivables = async (customerId) => {
    if (!customerId) {
      setReceivables([]);
      return;
    }
    try {
      const res = await api(`/api/ar?customer_id=${customerId}&status=open`);
      if (res.ok) {
        const data = await res.json();
        setReceivables(data.items || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCustomerChange = (customerId) => {
    setForm(prev => ({ ...prev, customer_id: customerId, items: [] }));
    loadReceivables(customerId);
  };

  const addReceivable = (ar) => {
    if (form.items.find(i => i.ar_id === ar.id)) {
      toast.error('Invoice sudah ditambahkan');
      return;
    }
    
    const newItem = {
      ar_id: ar.id,
      invoice_number: ar.invoice_number || ar.ar_number,
      date: ar.created_at,
      due_date: ar.due_date,
      remaining: ar.remaining_amount || ar.amount,
      discount: 0,
      payment: ar.remaining_amount || ar.amount,
    };
    
    setForm(prev => ({
      ...prev,
      items: [...prev.items, newItem]
    }));
  };

  const updateItem = (index, field, value) => {
    setForm(prev => {
      const newItems = [...prev.items];
      newItems[index] = { ...newItems[index], [field]: parseFloat(value) || 0 };
      
      const totalDiscount = newItems.reduce((acc, i) => acc + (i.discount || 0), 0);
      const totalPayment = newItems.reduce((acc, i) => acc + (i.payment || 0), 0);
      
      return { ...prev, items: newItems, total_discount: totalDiscount, total_payment: totalPayment };
    });
  };

  const removeItem = (index) => {
    setForm(prev => {
      const newItems = prev.items.filter((_, i) => i !== index);
      const totalDiscount = newItems.reduce((acc, i) => acc + (i.discount || 0), 0);
      const totalPayment = newItems.reduce((acc, i) => acc + (i.payment || 0), 0);
      return { ...prev, items: newItems, total_discount: totalDiscount, total_payment: totalPayment };
    });
  };

  const handleSave = async () => {
    if (!form.customer_id) {
      toast.error('Pilih pelanggan');
      return;
    }
    if (form.items.length === 0) {
      toast.error('Tambahkan minimal 1 invoice');
      return;
    }
    
    setSaving(true);
    try {
      const payload = {
        customer_id: form.customer_id,
        account_id: form.account_id,
        payment_method: form.payment_method,
        reference_no: form.reference_no,
        notes: form.notes,
        items: form.items.map(i => ({
          ar_id: i.ar_id,
          discount_amount: i.discount,
          payment_amount: i.payment,
        })),
        total_discount: form.total_discount,
        total_amount: form.total_payment,
      };
      
      const res = await api('/api/ar/payments', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        toast.success('Pembayaran piutang berhasil disimpan');
        navigate('/sales/ar-payments');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menyimpan');
      }
    } catch (err) {
      console.error(err);
      toast.error('Terjadi kesalahan');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin" /></div>;
  }

  return (
    <div className="space-y-4 p-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <Wallet className="h-5 w-5 text-blue-400" />
          Tambah Pembayaran Piutang
        </h2>
        <button onClick={() => navigate('/sales/ar-payments')} className="p-2 hover:bg-gray-700 rounded">
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Header */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4">
        <div className="grid grid-cols-4 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">No Transaksi</label>
            <input type="text" value={form.payment_number} disabled className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Pelanggan <span className="text-red-400">*</span></label>
            <select value={form.customer_id} onChange={e => handleCustomerChange(e.target.value)} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm">
              <option value="">Pilih Pelanggan</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.code} - {c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Kode Akun</label>
            <select value={form.account_id} onChange={e => setForm(p => ({...p, account_id: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm">
              <option value="">Pilih Akun Kas/Bank</option>
              {accounts.map(a => <option key={a.id} value={a.id}>{a.code} - {a.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Cara Bayar</label>
            <select value={form.payment_method} onChange={e => setForm(p => ({...p, payment_method: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm">
              <option value="cash">Tunai</option>
              <option value="transfer">Transfer</option>
              <option value="giro">Giro</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tanggal</label>
            <input type="date" value={form.date} onChange={e => setForm(p => ({...p, date: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">No Referensi</label>
            <input type="text" value={form.reference_no} onChange={e => setForm(p => ({...p, reference_no: e.target.value}))} placeholder="No Giro/Transfer" className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Keterangan</label>
            <input type="text" value={form.notes} onChange={e => setForm(p => ({...p, notes: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
        </div>
      </div>

      {/* Outstanding Receivables */}
      {form.customer_id && receivables.length > 0 && (
        <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
          <p className="text-sm text-gray-400 mb-2">Invoice Belum Lunas:</p>
          <div className="flex flex-wrap gap-2">
            {receivables.map(ar => (
              <button
                key={ar.id}
                onClick={() => addReceivable(ar)}
                className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded"
              >
                {ar.invoice_number || ar.ar_number} - {formatRupiah(ar.remaining_amount || ar.amount)}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Items Grid */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-800">
              <tr className="text-left text-gray-400 text-xs">
                <th className="p-2 border-b border-gray-700">No Transaksi</th>
                <th className="p-2 border-b border-gray-700">Tanggal</th>
                <th className="p-2 border-b border-gray-700">Tanggal JT</th>
                <th className="p-2 border-b border-gray-700 text-right">Sisa</th>
                <th className="p-2 border-b border-gray-700 text-right w-28">Potongan</th>
                <th className="p-2 border-b border-gray-700 text-right w-32">Jumlah Bayar</th>
                <th className="p-2 border-b border-gray-700 w-10"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {form.items.length === 0 ? (
                <tr><td colSpan="7" className="p-4 text-center text-gray-400">Pilih invoice dari daftar di atas</td></tr>
              ) : form.items.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-800/30">
                  <td className="p-2 text-blue-400">{item.invoice_number}</td>
                  <td className="p-2">{formatDate(item.date)}</td>
                  <td className="p-2">{formatDate(item.due_date)}</td>
                  <td className="p-2 text-right">{formatRupiah(item.remaining)}</td>
                  <td className="p-2">
                    <input type="number" min="0" value={item.discount} onChange={e => updateItem(idx, 'discount', e.target.value)} className="w-full px-2 py-1 bg-gray-800 border border-gray-600 rounded text-right text-sm" />
                  </td>
                  <td className="p-2">
                    <input type="number" min="0" value={item.payment} onChange={e => updateItem(idx, 'payment', e.target.value)} className="w-full px-2 py-1 bg-gray-800 border border-gray-600 rounded text-right text-sm" />
                  </td>
                  <td className="p-2">
                    <button onClick={() => removeItem(idx)} className="p-1 hover:bg-red-700 rounded">
                      <Trash2 className="h-3.5 w-3.5 text-red-400" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Totals */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4">
        <div className="grid grid-cols-3 gap-4 text-right">
          <div>
            <p className="text-xs text-gray-400">Total Potongan</p>
            <p className="text-xl font-bold text-red-400">{formatRupiah(form.total_discount)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400">Total Bayar</p>
            <p className="text-2xl font-bold text-green-400">{formatRupiah(form.total_payment)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400">Status</p>
            <p className="text-lg font-medium text-blue-400">
              {form.items.every(i => i.payment >= i.remaining - i.discount) ? 'LUNAS' : 'SEBAGIAN'}
            </p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center bg-gray-800/50 rounded-lg border border-gray-700 p-4">
        <button onClick={() => navigate('/sales/ar-payments')} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2">
          <X className="h-4 w-4" /> Batal
        </button>
        <button onClick={handleSave} disabled={saving} className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded flex items-center gap-2 font-medium disabled:opacity-50">
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          Simpan
        </button>
      </div>
    </div>
  );
};

export default ARPaymentAdd;
