import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Plus, Search, Save, X, Loader2, FileText, Trash2, Calendar, 
  User, Clock, Percent, Warehouse, Printer, Package
} from 'lucide-react';
import { toast } from 'sonner';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

const SalesOrderAdd = () => {
  const { api, user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const itemInputRef = useRef(null);

  // Master data
  const [customers, setCustomers] = useState([]);
  const [salesPersons, setSalesPersons] = useState([]);
  const [products, setProducts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);

  // Form state
  const [form, setForm] = useState({
    order_number: '',
    date: new Date().toISOString().split('T')[0],
    time: new Date().toTimeString().slice(0, 5),
    customer_id: '',
    sales_person_id: '',
    warehouse_id: '',
    delivery_date: '',
    ppn_type: 'exclude',
    ppn_percent: 11,
    notes: '',
    items: [],
    // Calculations
    subtotal: 0,
    discount_amount: 0,
    tax_amount: 0,
    other_cost: 0,
    dp_amount: 0,
    grand_total: 0,
  });

  // Load master data
  useEffect(() => {
    const loadMasterData = async () => {
      try {
        const [custRes, salesRes, prodRes, whRes] = await Promise.all([
          api('/api/customers'),
          api('/api/sales-persons'),
          api('/api/products?limit=2000'),
          api('/api/master/warehouses')
        ]);
        
        if (custRes.ok) setCustomers((await custRes.json()).items || []);
        if (salesRes.ok) setSalesPersons((await salesRes.json()) || []);
        if (prodRes.ok) setProducts((await prodRes.json()).items || []);
        if (whRes.ok) setWarehouses(await whRes.json() || []);
        
        // Generate order number
        const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        const seq = String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0');
        setForm(prev => ({ ...prev, order_number: `SO-${dateStr}-${seq}` }));
      } catch (err) {
        console.error(err);
        toast.error('Gagal memuat data master');
      } finally {
        setLoading(false);
      }
    };
    loadMasterData();
  }, [api]);

  // Add item
  const addItem = (product) => {
    if (form.items.find(i => i.product_id === product.id)) {
      toast.error('Item sudah ada');
      return;
    }
    
    const newItem = {
      no: form.items.length + 1,
      product_id: product.id,
      product_code: product.code,
      product_name: product.name,
      item_type: product.item_type || 'barang',
      qty_order: 1,
      qty_delivered: 0,
      unit: product.unit || 'PCS',
      unit_price: product.sell_price || 0,
      discount_percent: 0,
      tax_percent: 0,
      subtotal: product.sell_price || 0,
    };
    
    setForm(prev => ({ ...prev, items: [...prev.items, newItem] }));
    toast.success(`${product.name} ditambahkan`);
  };

  // Update item
  const updateItem = (index, field, value) => {
    setForm(prev => {
      const newItems = [...prev.items];
      newItems[index] = { ...newItems[index], [field]: value };
      
      // Recalculate
      const item = newItems[index];
      const qty = parseFloat(item.qty_order) || 0;
      const price = parseFloat(item.unit_price) || 0;
      const discPct = parseFloat(item.discount_percent) || 0;
      
      const itemSubtotal = qty * price;
      const discAmount = itemSubtotal * (discPct / 100);
      newItems[index].subtotal = itemSubtotal - discAmount;
      
      return { ...prev, items: newItems };
    });
  };

  // Remove item
  const removeItem = (index) => {
    setForm(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index).map((item, i) => ({ ...item, no: i + 1 }))
    }));
  };

  // Calculate totals
  const calculateTotals = () => {
    let subtotal = 0;
    form.items.forEach(item => {
      subtotal += item.subtotal || 0;
    });
    
    const discAmt = parseFloat(form.discount_amount) || 0;
    const afterDisc = subtotal - discAmt;
    const taxAmt = afterDisc * (parseFloat(form.ppn_percent) || 0) / 100;
    const otherCost = parseFloat(form.other_cost) || 0;
    const grandTotal = afterDisc + taxAmt + otherCost;
    
    return { subtotal, taxAmt, grandTotal };
  };

  const totals = calculateTotals();

  // Save
  const handleSave = async () => {
    if (!form.customer_id) {
      toast.error('Pilih pelanggan');
      return;
    }
    if (form.items.length === 0) {
      toast.error('Tambahkan minimal 1 item');
      return;
    }
    
    setSaving(true);
    try {
      const payload = {
        customer_id: form.customer_id,
        sales_person_id: form.sales_person_id,
        warehouse_id: form.warehouse_id,
        delivery_date: form.delivery_date,
        ppn_type: form.ppn_type,
        ppn_percent: form.ppn_percent,
        notes: form.notes,
        items: form.items.map(item => ({
          product_id: item.product_id,
          quantity: item.qty_order,
          unit_price: item.unit_price,
          discount_percent: item.discount_percent,
        })),
        subtotal: totals.subtotal,
        tax_amount: totals.taxAmt,
        total: totals.grandTotal,
        dp_amount: form.dp_amount,
      };
      
      const res = await api('/api/sales/orders', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const result = await res.json();
        toast.success(`Pesanan ${result.order_number || form.order_number} berhasil disimpan`);
        navigate('/sales/orders');
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
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4" data-testid="sales-order-add">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <FileText className="h-5 w-5 text-blue-400" />
          Tambah Pesanan Penjualan
        </h2>
        <button onClick={() => navigate('/sales/orders')} className="p-2 hover:bg-gray-700 rounded">
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Form Header */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4">
        <div className="grid grid-cols-6 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">No Transaksi</label>
            <input type="text" value={form.order_number} disabled className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tanggal</label>
            <input type="date" value={form.date} onChange={e => setForm(p => ({...p, date: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Keluar Dari Gudang</label>
            <select value={form.warehouse_id} onChange={e => setForm(p => ({...p, warehouse_id: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm">
              <option value="">Pilih Gudang</option>
              {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Pelanggan <span className="text-red-400">*</span></label>
            <select value={form.customer_id} onChange={e => setForm(p => ({...p, customer_id: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm">
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
            <label className="block text-xs text-gray-400 mb-1">PPN</label>
            <select value={form.ppn_type} onChange={e => setForm(p => ({...p, ppn_type: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm">
              <option value="exclude">Exclude PPN</option>
              <option value="include">Include PPN</option>
            </select>
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tgl Kirim</label>
            <input type="date" value={form.delivery_date} onChange={e => setForm(p => ({...p, delivery_date: e.target.value}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
          <div className="col-span-2">
            <label className="block text-xs text-gray-400 mb-1">Keterangan</label>
            <input type="text" value={form.notes} onChange={e => setForm(p => ({...p, notes: e.target.value}))} placeholder="Catatan..." className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
        </div>
      </div>

      {/* Item Input */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              ref={itemInputRef}
              type="text"
              placeholder="Scan barcode atau ketik kode/nama item lalu Enter..."
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded text-white"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const found = products.find(p => 
                    p.code?.toLowerCase() === e.target.value.toLowerCase() ||
                    p.barcode?.toLowerCase() === e.target.value.toLowerCase() ||
                    p.name?.toLowerCase().includes(e.target.value.toLowerCase())
                  );
                  if (found) {
                    addItem(found);
                    e.target.value = '';
                  } else {
                    toast.error('Item tidak ditemukan');
                  }
                }
              }}
            />
          </div>
        </div>
        
        {/* Quick product buttons */}
        <div className="mt-2 flex flex-wrap gap-1 max-h-20 overflow-y-auto">
          {products.slice(0, 20).map(p => (
            <button
              key={p.id}
              onClick={() => addItem(p)}
              className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded truncate max-w-32"
            >
              {p.code} - {p.name}
            </button>
          ))}
        </div>
      </div>

      {/* Items Grid */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto max-h-64">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 sticky top-0">
              <tr className="text-left text-gray-400 text-xs">
                <th className="p-2 border-b border-gray-700 w-10">No</th>
                <th className="p-2 border-b border-gray-700">Kode Item</th>
                <th className="p-2 border-b border-gray-700">Keterangan</th>
                <th className="p-2 border-b border-gray-700">Jenis</th>
                <th className="p-2 border-b border-gray-700 text-right w-20">Jumlah</th>
                <th className="p-2 border-b border-gray-700 text-right w-16">Jml Terima</th>
                <th className="p-2 border-b border-gray-700 w-16">Satuan</th>
                <th className="p-2 border-b border-gray-700 text-right w-28">Harga</th>
                <th className="p-2 border-b border-gray-700 text-right w-16">Pot (%)</th>
                <th className="p-2 border-b border-gray-700 text-right w-28">Total</th>
                <th className="p-2 border-b border-gray-700 text-right w-16">Tax (%)</th>
                <th className="p-2 border-b border-gray-700 w-10"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {form.items.length === 0 ? (
                <tr><td colSpan="12" className="p-4 text-center text-gray-400">Belum ada item</td></tr>
              ) : form.items.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-800/30">
                  <td className="p-2 text-center">{item.no}</td>
                  <td className="p-2 font-mono">{item.product_code}</td>
                  <td className="p-2">{item.product_name}</td>
                  <td className="p-2 text-xs">{item.item_type}</td>
                  <td className="p-2">
                    <input type="number" min="1" value={item.qty_order} onChange={e => updateItem(idx, 'qty_order', parseInt(e.target.value) || 0)} className="w-full px-1 py-0.5 bg-gray-800 border border-gray-600 rounded text-right text-sm" />
                  </td>
                  <td className="p-2 text-right text-green-400">{item.qty_delivered || 0}</td>
                  <td className="p-2">{item.unit}</td>
                  <td className="p-2">
                    <input type="number" min="0" value={item.unit_price} onChange={e => updateItem(idx, 'unit_price', parseFloat(e.target.value) || 0)} className="w-full px-1 py-0.5 bg-gray-800 border border-gray-600 rounded text-right text-sm" />
                  </td>
                  <td className="p-2">
                    <input type="number" min="0" max="100" value={item.discount_percent} onChange={e => updateItem(idx, 'discount_percent', parseFloat(e.target.value) || 0)} className="w-full px-1 py-0.5 bg-gray-800 border border-gray-600 rounded text-right text-sm" />
                  </td>
                  <td className="p-2 text-right font-medium">{formatRupiah(item.subtotal)}</td>
                  <td className="p-2">
                    <input type="number" min="0" max="100" value={item.tax_percent || 0} onChange={e => updateItem(idx, 'tax_percent', parseFloat(e.target.value) || 0)} className="w-full px-1 py-0.5 bg-gray-800 border border-gray-600 rounded text-right text-sm" />
                  </td>
                  <td className="p-2">
                    <button onClick={() => removeItem(idx)} className="p-0.5 hover:bg-red-700 rounded">
                      <Trash2 className="h-3.5 w-3.5 text-red-400" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer Calculations */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-gray-800/50 rounded-lg border border-gray-700 p-4">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Potongan Nominal</label>
              <input type="number" value={form.discount_amount} onChange={e => setForm(p => ({...p, discount_amount: parseFloat(e.target.value) || 0}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">PPN %</label>
              <input type="number" value={form.ppn_percent} onChange={e => setForm(p => ({...p, ppn_percent: parseFloat(e.target.value) || 0}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Biaya Lain</label>
              <input type="number" value={form.other_cost} onChange={e => setForm(p => ({...p, other_cost: parseFloat(e.target.value) || 0}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Titip / DP</label>
              <input type="number" value={form.dp_amount} onChange={e => setForm(p => ({...p, dp_amount: parseFloat(e.target.value) || 0}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
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
              <span className="text-xl font-bold text-green-400">{formatRupiah(totals.grandTotal)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center bg-gray-800/50 rounded-lg border border-gray-700 p-4">
        <div className="flex gap-2">
          <button onClick={() => navigate('/sales/orders')} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2">
            <X className="h-4 w-4" /> Batal
          </button>
        </div>
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

export default SalesOrderAdd;
