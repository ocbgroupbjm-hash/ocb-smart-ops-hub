import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Plus, Search, Save, X, Loader2, FileText, Trash2, Calendar, 
  User, Clock, Percent, Warehouse, Printer, Package, CreditCard,
  Banknote, DollarSign
} from 'lucide-react';
import { toast } from 'sonner';
import { SearchableSelect } from '../../components/ui/searchable-select';
import { SearchableEnumSelect } from '../../components/ui/searchable-enum-select';
import { DatePickerWithDefault } from '../../components/ui/date-picker-default';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

const SalesAdd = () => {
  const { api, user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const itemInputRef = useRef(null);

  // Master data
  const [customers, setCustomers] = useState([]);
  const [salesPersons, setSalesPersons] = useState([]);
  const [products, setProducts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [salesOrders, setSalesOrders] = useState([]);
  
  // Convert master data to options format for SearchableSelect
  const customerOptions = useMemo(() => 
    customers.map(c => ({ value: c.id, label: c.name, sublabel: c.code })),
    [customers]
  );
  
  const salesPersonOptions = useMemo(() => 
    salesPersons.map(s => ({ value: s.id, label: s.name, sublabel: s.code })),
    [salesPersons]
  );
  
  const warehouseOptions = useMemo(() => 
    warehouses.map(w => ({ value: w.id, label: w.name, sublabel: w.code })),
    [warehouses]
  );
  
  const productOptions = useMemo(() => 
    products.map(p => ({ 
      value: p.id, 
      label: p.name, 
      sublabel: `${p.code || ''} | Stok: ${p.stock || 0} | Rp ${(p.sell_price || 0).toLocaleString()}`,
      code: p.code,
      barcode: p.barcode,
      product: p
    })),
    [products]
  );
  
  const salesOrderOptions = useMemo(() => 
    salesOrders.map(so => ({ value: so.id, label: `${so.order_number} - ${so.customer_name}` })),
    [salesOrders]
  );
  
  // PPN options
  const ppnTypeOptions = [
    { value: 'exclude', label: 'Exclude PPN' },
    { value: 'include', label: 'Include PPN' },
  ];

  // Form state
  const [form, setForm] = useState({
    invoice_number: '',
    date: new Date().toISOString().split('T')[0],
    time: new Date().toTimeString().slice(0, 5),
    sales_order_id: searchParams.get('so_id') || '',
    customer_id: '',
    sales_person_id: '',
    warehouse_id: '',
    ppn_type: 'exclude',
    ppn_percent: 11,
    notes: '',
    voucher_code: '',
    items: [],
    // Calculations
    subtotal: 0,
    discount_amount: 0,
    tax_amount: 0,
    other_cost: 0,
    grand_total: 0,
    // Payment
    dp_from_so: 0,
    deposit_used: 0,
    cash_amount: 0,
    credit_amount: 0,
    payment_type: 'cash', // cash, credit, combo
  });

  const [activeTab, setActiveTab] = useState('rincian');
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  // Load master data
  useEffect(() => {
    const loadMasterData = async () => {
      try {
        const [custRes, salesRes, prodRes, whRes, soRes] = await Promise.all([
          api('/api/customers'),
          api('/api/master/sales-persons'),
          api('/api/products?limit=2000'),
          api('/api/master/warehouses'),
          api('/api/sales/orders?status=confirmed')
        ]);
        
        if (custRes.ok) setCustomers((await custRes.json()).items || []);
        if (salesRes.ok) setSalesPersons((await salesRes.json()) || []);
        if (prodRes.ok) setProducts((await prodRes.json()).items || []);
        if (whRes.ok) setWarehouses(await whRes.json() || []);
        if (soRes.ok) setSalesOrders((await soRes.json()).items || []);
        
        // Generate invoice number
        const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        const seq = String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0');
        setForm(prev => ({ ...prev, invoice_number: `INV-${dateStr}-${seq}` }));
      } catch (err) {
        console.error(err);
        toast.error('Gagal memuat data master');
      } finally {
        setLoading(false);
      }
    };
    loadMasterData();
  }, [api]);

  // Load SO if selected
  const loadSalesOrder = async (soId) => {
    if (!soId) return;
    try {
      const res = await api(`/api/sales/orders/${soId}`);
      if (res.ok) {
        const so = await res.json();
        setForm(prev => ({
          ...prev,
          customer_id: so.customer_id,
          sales_person_id: so.sales_person_id,
          warehouse_id: so.warehouse_id,
          dp_from_so: so.dp_amount || 0,
          items: (so.items || []).map((item, idx) => ({
            no: idx + 1,
            product_id: item.product_id,
            product_code: item.product_code,
            product_name: item.product_name,
            item_type: item.item_type || 'barang',
            qty_from_so: item.quantity,
            qty: item.quantity - (item.delivered_qty || 0),
            unit: item.unit || 'PCS',
            unit_price: item.unit_price,
            discount_percent: item.discount_percent || 0,
            tax_percent: item.tax_percent || 0,
            subtotal: (item.quantity - (item.delivered_qty || 0)) * item.unit_price,
          }))
        }));
        toast.success(`Data dari SO ${so.order_number} dimuat`);
      }
    } catch (err) {
      console.error(err);
    }
  };

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
      qty_from_so: 0,
      qty: 1,
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
      
      const item = newItems[index];
      const qty = parseFloat(item.qty) || 0;
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
    let itemTax = 0;
    form.items.forEach(item => {
      subtotal += item.subtotal || 0;
      itemTax += (item.subtotal || 0) * (parseFloat(item.tax_percent) || 0) / 100;
    });
    
    const discAmt = parseFloat(form.discount_amount) || 0;
    const afterDisc = subtotal - discAmt;
    const taxAmt = afterDisc * (parseFloat(form.ppn_percent) || 0) / 100 + itemTax;
    const otherCost = parseFloat(form.other_cost) || 0;
    const grandTotal = afterDisc + taxAmt + otherCost;
    
    return { subtotal, taxAmt, grandTotal };
  };

  const totals = calculateTotals();

  // Save
  const handleSave = async (withPayment = false) => {
    if (!form.customer_id) {
      toast.error('Pilih pelanggan');
      return;
    }
    if (form.items.length === 0) {
      toast.error('Tambahkan minimal 1 item');
      return;
    }
    
    // Validate stock
    for (const item of form.items) {
      if (item.qty <= 0) {
        toast.error(`Qty untuk ${item.product_name} harus > 0`);
        return;
      }
    }
    
    if (withPayment) {
      setShowPaymentModal(true);
      return;
    }
    
    setSaving(true);
    try {
      const payload = {
        sales_order_id: form.sales_order_id || null,
        customer_id: form.customer_id,
        sales_person_id: form.sales_person_id,
        warehouse_id: form.warehouse_id,
        ppn_type: form.ppn_type,
        ppn_percent: form.ppn_percent,
        notes: form.notes,
        voucher_code: form.voucher_code,
        items: form.items.map(item => ({
          product_id: item.product_id,
          quantity: item.qty,
          unit_price: item.unit_price,
          discount_percent: item.discount_percent,
          tax_percent: item.tax_percent,
        })),
        subtotal: totals.subtotal,
        discount_amount: form.discount_amount,
        tax_amount: totals.taxAmt,
        other_cost: form.other_cost,
        total: totals.grandTotal,
        payment_type: form.payment_type,
        cash_amount: form.cash_amount,
        credit_amount: totals.grandTotal - form.cash_amount - form.dp_from_so - form.deposit_used,
        dp_used: form.dp_from_so,
        deposit_used: form.deposit_used,
      };
      
      const res = await api('/api/sales/invoices', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const result = await res.json();
        toast.success(`Penjualan ${result.invoice_number || form.invoice_number} berhasil disimpan`);
        navigate('/sales/list');
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

  // Process payment
  const processPayment = async () => {
    setShowPaymentModal(false);
    await handleSave(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4" data-testid="sales-add">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <FileText className="h-5 w-5 text-blue-400" />
          Tambah Penjualan
        </h2>
        <button onClick={() => navigate('/sales/list')} className="p-2 hover:bg-gray-700 rounded">
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Form Header */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4">
        <div className="grid grid-cols-6 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">No Transaksi</label>
            <input type="text" value={form.invoice_number} disabled className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tanggal</label>
            <DatePickerWithDefault
              value={form.date}
              onValueChange={(val) => setForm(p => ({...p, date: val}))}
              defaultToday={true}
              data-testid="sales-date"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Pesanan (SO)</label>
            <SearchableSelect
              options={salesOrderOptions}
              value={form.sales_order_id}
              onValueChange={(val) => { setForm(p => ({...p, sales_order_id: val})); if(val) loadSalesOrder(val); }}
              placeholder="Tanpa SO"
              searchPlaceholder="Cari SO..."
              data-testid="so-select"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Keluar Dari Gudang</label>
            <SearchableSelect
              options={warehouseOptions}
              value={form.warehouse_id}
              onValueChange={(val) => setForm(p => ({...p, warehouse_id: val}))}
              placeholder="Pilih Gudang"
              searchPlaceholder="Cari gudang..."
              data-testid="warehouse-select"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Pelanggan <span className="text-red-400">*</span></label>
            <SearchableSelect
              options={customerOptions}
              value={form.customer_id}
              onValueChange={(val) => setForm(p => ({...p, customer_id: val}))}
              placeholder="Pilih Pelanggan"
              searchPlaceholder="Ketik nama pelanggan..."
              data-testid="customer-select"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sales</label>
            <SearchableSelect
              options={salesPersonOptions}
              value={form.sales_person_id}
              onValueChange={(val) => setForm(p => ({...p, sales_person_id: val}))}
              placeholder="Pilih Sales"
              searchPlaceholder="Ketik nama sales..."
              data-testid="salesperson-select"
            />
          </div>
        </div>
        
        <div className="grid grid-cols-4 gap-4 mt-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">PPN</label>
            <SearchableEnumSelect
              options={ppnTypeOptions}
              value={form.ppn_type}
              onValueChange={(val) => setForm(p => ({...p, ppn_type: val}))}
              placeholder="Pilih PPN"
              data-testid="ppn-type-select"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Voucher</label>
            <input type="text" value={form.voucher_code} onChange={e => setForm(p => ({...p, voucher_code: e.target.value}))} placeholder="Kode voucher" className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
          <div className="col-span-2">
            <label className="block text-xs text-gray-400 mb-1">Keterangan</label>
            <input type="text" value={form.notes} onChange={e => setForm(p => ({...p, notes: e.target.value}))} placeholder="Catatan..." className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
          </div>
        </div>
      </div>

      {/* Item Input - Searchable Product Select */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <SearchableSelect
              options={productOptions}
              value=""
              onValueChange={(val) => {
                if (val) {
                  const found = products.find(p => p.id === val);
                  if (found) {
                    addItem(found);
                  }
                }
              }}
              placeholder="Klik untuk pilih item, atau ketik nama/kode item..."
              searchPlaceholder="Ketik nama atau kode item..."
              emptyText="Item tidak ditemukan"
              allowClear={false}
              data-testid="item-search"
            />
          </div>
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
                <th className="p-2 border-b border-gray-700 text-right w-16">Pesanan</th>
                <th className="p-2 border-b border-gray-700 text-right w-20">Jumlah</th>
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
                  <td className="p-2 text-right text-gray-400">{item.qty_from_so || '-'}</td>
                  <td className="p-2">
                    <input type="number" min="1" value={item.qty} onChange={e => updateItem(idx, 'qty', parseInt(e.target.value) || 0)} className="w-full px-1 py-0.5 bg-gray-800 border border-gray-600 rounded text-right text-sm" />
                  </td>
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

      {/* Bottom Tabs */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="flex border-b border-gray-700">
          <button onClick={() => setActiveTab('rincian')} className={`px-4 py-2 text-sm ${activeTab === 'rincian' ? 'bg-blue-600/20 text-blue-400 border-b-2 border-blue-500' : 'text-gray-400'}`}>Rincian</button>
          <button onClick={() => setActiveTab('potongan')} className={`px-4 py-2 text-sm ${activeTab === 'potongan' ? 'bg-blue-600/20 text-blue-400 border-b-2 border-blue-500' : 'text-gray-400'}`}>Potongan</button>
        </div>
        <div className="p-3">
          {activeTab === 'rincian' && (
            <p className="text-gray-400 text-sm">Pilih item di grid untuk melihat rincian</p>
          )}
          {activeTab === 'potongan' && (
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
            </div>
          )}
        </div>
      </div>

      {/* Footer Calculations */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-gray-800/50 rounded-lg border border-gray-700 p-4">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">DP SO</label>
              <input type="number" value={form.dp_from_so} disabled className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Deposit</label>
              <input type="number" value={form.deposit_used} onChange={e => setForm(p => ({...p, deposit_used: parseFloat(e.target.value) || 0}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Tunai / DP</label>
              <input type="number" value={form.cash_amount} onChange={e => setForm(p => ({...p, cash_amount: parseFloat(e.target.value) || 0}))} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Kredit</label>
              <input type="number" value={Math.max(0, totals.grandTotal - form.cash_amount - form.dp_from_so - form.deposit_used)} disabled className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm" />
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
              <span className="text-gray-400">Potongan</span>
              <span className="text-red-400">-{formatRupiah(form.discount_amount)}</span>
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
          <button onClick={() => navigate('/sales/list')} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2">
            <X className="h-4 w-4" /> Batal
          </button>
          <button className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded flex items-center gap-2">
            <Package className="h-4 w-4" /> Detail Item
          </button>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded flex items-center gap-2">
            <Printer className="h-4 w-4" /> Cetak
          </button>
          <button onClick={() => handleSave(false)} disabled={saving} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2 disabled:opacity-50">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Simpan
          </button>
          <button onClick={() => handleSave(true)} disabled={saving} className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded flex items-center gap-2 font-medium disabled:opacity-50">
            <DollarSign className="h-4 w-4" /> Bayar
          </button>
        </div>
      </div>

      {/* Payment Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96 border border-gray-700">
            <h3 className="text-lg font-bold mb-4">Pembayaran</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Total Tagihan</label>
                <p className="text-2xl font-bold text-green-400">{formatRupiah(totals.grandTotal)}</p>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jenis Pembayaran</label>
                <select value={form.payment_type} onChange={e => setForm(p => ({...p, payment_type: e.target.value}))} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white">
                  <option value="cash">Tunai</option>
                  <option value="credit">Kredit</option>
                  <option value="combo">Kombinasi</option>
                </select>
              </div>
              {(form.payment_type === 'cash' || form.payment_type === 'combo') && (
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Jumlah Tunai</label>
                  <input type="number" value={form.cash_amount} onChange={e => setForm(p => ({...p, cash_amount: parseFloat(e.target.value) || 0}))} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white" />
                </div>
              )}
              <div className="flex gap-2 pt-4">
                <button onClick={() => setShowPaymentModal(false)} className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded">Batal</button>
                <button onClick={processPayment} className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded font-medium">Proses</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesAdd;
