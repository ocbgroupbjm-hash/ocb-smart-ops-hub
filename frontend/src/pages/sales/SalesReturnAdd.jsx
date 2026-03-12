import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Save, X, Loader2, RotateCcw, Trash2, Search, Printer
} from 'lucide-react';
import { toast } from 'sonner';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

const SalesReturnAdd = () => {
  const { api, user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [customers, setCustomers] = useState([]);
  const [salesPersons, setSalesPersons] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [invoices, setInvoices] = useState([]);

  const [form, setForm] = useState({
    return_number: '',
    date: new Date().toISOString().split('T')[0],
    customer_id: '',
    sales_person_id: '',
    warehouse_id: '',
    ppn_type: 'exclude',
    notes: '',
    items: [],
    subtotal: 0,
    discount_amount: 0,
    tax_amount: 0,
    other_cost: 0,
    grand_total: 0,
    refund_type: 'ar_deduct', // ar_deduct, cash, deposit
    cash_refund: 0,
    deposit_add: 0,
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        const [custRes, salesRes, whRes] = await Promise.all([
          api('/api/customers'),
          api('/api/master/sales-persons'),
          api('/api/master/warehouses')
        ]);
        
        if (custRes.ok) setCustomers((await custRes.json()).items || []);
        if (salesRes.ok) setSalesPersons((await salesRes.json()) || []);
        if (whRes.ok) setWarehouses(await whRes.json() || []);
        
        const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        const seq = String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0');
        setForm(prev => ({ ...prev, return_number: `SRT-${dateStr}-${seq}` }));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [api]);

  const loadInvoices = async (customerId) => {
    if (!customerId) {
      setInvoices([]);
      return;
    }
    try {
      const res = await api(`/api/sales/invoices?customer_id=${customerId}`);
      if (res.ok) {
        const data = await res.json();
        setInvoices(data.items || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCustomerChange = (customerId) => {
    setForm(prev => ({ ...prev, customer_id: customerId, items: [] }));
    loadInvoices(customerId);
  };

  const addItemFromInvoice = (invoice, item) => {
    const existing = form.items.find(i => i.product_id === item.product_id && i.invoice_id === invoice.id);
    if (existing) {
      toast.error('Item sudah ditambahkan');
      return;
    }
    
    const newItem = {
      invoice_id: invoice.id,
      invoice_number: invoice.invoice_number,
      product_id: item.product_id,
      product_code: item.product_code,
      product_name: item.product_name,
      item_type: item.item_type || 'barang',
      qty_sold: item.quantity,
      unit_sold: item.unit,
      qty_return: 1,
      unit: item.unit,
      unit_price: item.unit_price,
      discount_percent: item.discount_percent || 0,
      subtotal: item.unit_price,
    };
    
    setForm(prev => ({
      ...prev,
      items: [...prev.items, newItem]
    }));
  };

  const updateItem = (index, field, value) => {
    setForm(prev => {
      const newItems = [...prev.items];
      newItems[index] = { ...newItems[index], [field]: value };
      
      const item = newItems[index];
      const qty = parseFloat(item.qty_return) || 0;
      const price = parseFloat(item.unit_price) || 0;
      const discPct = parseFloat(item.discount_percent) || 0;
      
      const itemSubtotal = qty * price;
      const discAmount = itemSubtotal * (discPct / 100);
      newItems[index].subtotal = itemSubtotal - discAmount;
      
      return { ...prev, items: newItems };
    });
  };

  const removeItem = (index) => {
    setForm(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const calculateTotals = () => {
    let subtotal = 0;
    form.items.forEach(item => {
      subtotal += item.subtotal || 0;
    });
    
    const discAmt = parseFloat(form.discount_amount) || 0;
    const afterDisc = subtotal - discAmt;
    const taxAmt = afterDisc * 11 / 100;
    const grandTotal = afterDisc + taxAmt;
    
    return { subtotal, taxAmt, grandTotal };
  };

  const totals = calculateTotals();

  const handleSave = async () => {
    if (!form.customer_id) {
      toast.error('Pilih pelanggan');
      return;
    }
    if (form.items.length === 0) {
      toast.error('Tambahkan minimal 1 item');
      return;
    }
    
    for (const item of form.items) {
      if (item.qty_return > item.qty_sold) {
        toast.error(`Qty retur untuk ${item.product_name} melebihi qty jual`);
        return;
      }
    }
    
    setSaving(true);
    try {
      const payload = {
        customer_id: form.customer_id,
        sales_person_id: form.sales_person_id,
        warehouse_id: form.warehouse_id,
        ppn_type: form.ppn_type,
        notes: form.notes,
        refund_type: form.refund_type,
        items: form.items.map(item => ({
          invoice_id: item.invoice_id,
          product_id: item.product_id,
          quantity: item.qty_return,
          unit_price: item.unit_price,
          discount_percent: item.discount_percent,
        })),
        subtotal: totals.subtotal,
        discount_amount: form.discount_amount,
        tax_amount: totals.taxAmt,
        total: totals.grandTotal,
        cash_refund: form.cash_refund,
        deposit_add: form.deposit_add,
      };
      
      const res = await api('/api/sales/returns', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        toast.success('Retur penjualan berhasil disimpan');
        navigate('/sales/returns');
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
          <RotateCcw className="h-5 w-5 text-blue-400" />
          Tambah Retur Penjualan
        </h2>
        <button onClick={() => navigate('/sales/returns')} className="p-2 hover:bg-gray-700 rounded">
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Header */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4">
        <div className="grid grid-cols-5 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">No Transaksi</label>
            <input type="text" value={form.return_number} disabled className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tanggal</label>
            <input type="date" value={form.date} onChange={e => setForm(p => ({...p, date: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Pelanggan <span className="text-red-400">*</span></label>
            <select value={form.customer_id} onChange={e => handleCustomerChange(e.target.value)} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm">
              <option value="">Pilih Pelanggan</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.code} - {c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sales</label>
            <select value={form.sales_person_id} onChange={e => setForm(p => ({...p, sales_person_id: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm">
              <option value="">Pilih Sales</option>
              {salesPersons.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Masuk ke Gudang</label>
            <select value={form.warehouse_id} onChange={e => setForm(p => ({...p, warehouse_id: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm">
              <option value="">Pilih Gudang</option>
              {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">PPN</label>
            <select value={form.ppn_type} onChange={e => setForm(p => ({...p, ppn_type: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm">
              <option value="exclude">Exclude PPN</option>
              <option value="include">Include PPN</option>
            </select>
          </div>
          <div className="col-span-2">
            <label className="block text-xs text-gray-400 mb-1">Keterangan</label>
            <input type="text" value={form.notes} onChange={e => setForm(p => ({...p, notes: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
        </div>
      </div>

      {/* Invoice Selection */}
      {form.customer_id && invoices.length > 0 && (
        <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
          <p className="text-sm text-gray-400 mb-2">Pilih item dari invoice:</p>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {invoices.map(inv => (
              <div key={inv.id} className="border border-gray-700 rounded p-2">
                <p className="text-sm text-blue-400 mb-1">{inv.invoice_number} - {new Date(inv.created_at).toLocaleDateString('id-ID')}</p>
                <div className="flex flex-wrap gap-1">
                  {(inv.items || []).map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => addItemFromInvoice(inv, item)}
                      className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded"
                    >
                      {item.product_code} ({item.quantity} {item.unit})
                    </button>
                  ))}
                </div>
              </div>
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
                <th className="p-2 border-b border-gray-700">No Transaksi Asal</th>
                <th className="p-2 border-b border-gray-700">Kode Item</th>
                <th className="p-2 border-b border-gray-700">Keterangan</th>
                <th className="p-2 border-b border-gray-700">Jenis</th>
                <th className="p-2 border-b border-gray-700 text-right">Jml Jual</th>
                <th className="p-2 border-b border-gray-700">Satuan Jual</th>
                <th className="p-2 border-b border-gray-700 text-right w-20">Jml Retur</th>
                <th className="p-2 border-b border-gray-700">Satuan</th>
                <th className="p-2 border-b border-gray-700 text-right">Harga</th>
                <th className="p-2 border-b border-gray-700 text-right">Pot (%)</th>
                <th className="p-2 border-b border-gray-700 text-right">Total</th>
                <th className="p-2 border-b border-gray-700 w-10"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {form.items.length === 0 ? (
                <tr><td colSpan="12" className="p-4 text-center text-gray-400">Pilih item dari invoice di atas</td></tr>
              ) : form.items.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-800/30">
                  <td className="p-2 text-blue-400">{item.invoice_number}</td>
                  <td className="p-2 font-mono">{item.product_code}</td>
                  <td className="p-2">{item.product_name}</td>
                  <td className="p-2 text-xs">{item.item_type}</td>
                  <td className="p-2 text-right">{item.qty_sold}</td>
                  <td className="p-2">{item.unit_sold}</td>
                  <td className="p-2">
                    <input type="number" min="1" max={item.qty_sold} value={item.qty_return} onChange={e => updateItem(idx, 'qty_return', parseInt(e.target.value) || 0)} className="w-full px-2 py-1 bg-gray-800 border border-gray-600 rounded text-right text-sm" />
                  </td>
                  <td className="p-2">{item.unit}</td>
                  <td className="p-2 text-right">{formatRupiah(item.unit_price)}</td>
                  <td className="p-2 text-right">{item.discount_percent}%</td>
                  <td className="p-2 text-right font-medium text-red-400">{formatRupiah(item.subtotal)}</td>
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

      {/* Footer */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-gray-800/50 rounded-lg border border-gray-700 p-4">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Deposit</label>
              <input type="number" value={form.deposit_add} onChange={e => setForm(p => ({...p, deposit_add: parseFloat(e.target.value) || 0}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Tunai</label>
              <input type="number" value={form.cash_refund} onChange={e => setForm(p => ({...p, cash_refund: parseFloat(e.target.value) || 0}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Pot. Piutang</label>
              <input type="number" value={Math.max(0, totals.grandTotal - form.cash_refund - form.deposit_add)} disabled className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
            </div>
          </div>
        </div>
        
        <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Sub Total</span>
              <span>{formatRupiah(totals.subtotal)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Pajak</span>
              <span>{formatRupiah(totals.taxAmt)}</span>
            </div>
            <div className="flex justify-between pt-2 border-t border-gray-700">
              <span className="font-medium">Total Akhir</span>
              <span className="text-xl font-bold text-red-400">{formatRupiah(totals.grandTotal)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center bg-gray-800/50 rounded-lg border border-gray-700 p-4">
        <button onClick={() => navigate('/sales/returns')} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2">
          <X className="h-4 w-4" /> Batal
        </button>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded flex items-center gap-2">
            <Printer className="h-4 w-4" /> Cetak
          </button>
          <button onClick={handleSave} disabled={saving} className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded flex items-center gap-2 font-medium disabled:opacity-50">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Simpan
          </button>
        </div>
      </div>
    </div>
  );
};

export default SalesReturnAdd;
