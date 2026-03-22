import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  DollarSign, Search, Loader2, X, Plus, CheckCircle, Trash2, ArrowUpRight,
  Receipt, CreditCard, Wallet, Calendar, Building2
} from 'lucide-react';
import { toast } from 'sonner';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (dateStr) => dateStr ? new Date(dateStr).toLocaleDateString('id-ID') : '-';

// Status Badge Component
const StatusBadge = ({ status }) => {
  const config = {
    open: { label: 'Terbuka', bg: 'bg-blue-500/20', text: 'text-blue-400' },
    partial: { label: 'Sebagian', bg: 'bg-amber-500/20', text: 'text-amber-400' },
    paid: { label: 'Lunas', bg: 'bg-emerald-500/20', text: 'text-emerald-400' },
    overdue: { label: 'Jatuh Tempo', bg: 'bg-rose-500/20', text: 'text-rose-400' },
  }[status] || { label: status, bg: 'bg-gray-500/20', text: 'text-gray-400' };
  
  return (
    <span className={`px-2 py-1 ${config.bg} ${config.text} rounded-full text-xs font-medium`}>
      {config.label}
    </span>
  );
};

const ARReceiptPage = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loadingInvoices, setLoadingInvoices] = useState(false);
  const [cashBankAccounts, setCashBankAccounts] = useState([]);
  const [receipts, setReceipts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  // Form state
  const [selectedInvoices, setSelectedInvoices] = useState([]);
  const [receiptDate, setReceiptDate] = useState(new Date().toISOString().split('T')[0]);
  const [paymentMethod, setPaymentMethod] = useState('transfer');
  const [selectedAccount, setSelectedAccount] = useState('');
  const [referenceNo, setReferenceNo] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    loadCustomers();
    loadCashBankAccounts();
    loadReceipts();
  }, []);

  const loadCustomers = async () => {
    try {
      const res = await api('/api/customers?limit=500');
      if (res.ok) {
        const data = await res.json();
        setCustomers(data.items || data || []);
      }
    } catch (err) {
      console.error('Load customers error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCashBankAccounts = async () => {
    try {
      const res = await api('/api/cashflow/accounts');
      if (res.ok) {
        const data = await res.json();
        setCashBankAccounts(data.accounts || []);
        if (data.accounts?.length > 0) {
          setSelectedAccount(data.accounts[0].account_code);
        }
      }
    } catch (err) {
      console.error('Load accounts error:', err);
    }
  };

  const loadReceipts = async () => {
    try {
      const res = await api('/api/ar/payments?limit=50');
      if (res.ok) {
        const data = await res.json();
        setReceipts(data.items || data || []);
      }
    } catch (err) {
      console.error('Load receipts error:', err);
    }
  };

  const loadCustomerInvoices = async (customerId) => {
    setLoadingInvoices(true);
    try {
      // Get unpaid AR invoices
      const res = await api(`/api/ar?customer_id=${customerId}&status=open,partial,overdue&limit=100`);
      if (res.ok) {
        const data = await res.json();
        setInvoices(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat invoice');
    } finally {
      setLoadingInvoices(false);
    }
  };

  const selectCustomer = (customer) => {
    setSelectedCustomer(customer);
    setSelectedInvoices([]);
    loadCustomerInvoices(customer.id);
  };

  const toggleInvoice = (invoice) => {
    const exists = selectedInvoices.find(i => i.invoice_id === invoice.id);
    if (exists) {
      setSelectedInvoices(selectedInvoices.filter(i => i.invoice_id !== invoice.id));
    } else {
      setSelectedInvoices([...selectedInvoices, {
        invoice_id: invoice.id,
        invoice_no: invoice.ar_number || invoice.invoice_no,
        outstanding: invoice.outstanding_amount || invoice.amount,
        allocated_amount: invoice.outstanding_amount || invoice.amount,
        discount_amount: 0
      }]);
    }
  };

  const updateAllocation = (invoiceId, field, value) => {
    setSelectedInvoices(selectedInvoices.map(inv => {
      if (inv.invoice_id === invoiceId) {
        const numValue = parseFloat(value) || 0;
        if (field === 'allocated_amount' && numValue > inv.outstanding) {
          toast.error('Alokasi tidak boleh melebihi sisa piutang');
          return inv;
        }
        return { ...inv, [field]: numValue };
      }
      return inv;
    }));
  };

  const removeInvoice = (invoiceId) => {
    setSelectedInvoices(selectedInvoices.filter(i => i.invoice_id !== invoiceId));
  };

  const totalReceipt = selectedInvoices.reduce((sum, inv) => sum + inv.allocated_amount, 0);
  const totalDiscount = selectedInvoices.reduce((sum, inv) => sum + inv.discount_amount, 0);

  const handleSubmit = async () => {
    if (!selectedCustomer) {
      toast.error('Pilih customer terlebih dahulu');
      return;
    }
    if (selectedInvoices.length === 0) {
      toast.error('Pilih minimal 1 invoice');
      return;
    }
    if (!selectedAccount) {
      toast.error('Pilih akun kas/bank');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        customer_id: selectedCustomer.id,
        receipt_date: receiptDate,
        payment_method: paymentMethod,
        account_code: selectedAccount,
        reference_no: referenceNo,
        notes: notes,
        allocations: selectedInvoices.map(inv => ({
          invoice_id: inv.invoice_id,
          invoice_no: inv.invoice_no,
          allocated_amount: inv.allocated_amount,
          discount_amount: inv.discount_amount
        }))
      };

      const res = await api('/api/cashflow/ar-receipt/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const result = await res.json();
        toast.success(`Penerimaan ${result.receipt_no} berhasil dibuat`);
        setSelectedInvoices([]);
        setReferenceNo('');
        setNotes('');
        setShowForm(false);
        loadReceipts();
        if (selectedCustomer) {
          loadCustomerInvoices(selectedCustomer.id);
        }
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal membuat penerimaan');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100" data-testid="page-title">Penerimaan Piutang</h1>
          <p className="text-gray-400">Kelola penerimaan pembayaran dari customer</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          data-testid="new-receipt-btn"
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg hover:from-emerald-500 hover:to-teal-500"
        >
          <Plus className="h-5 w-5" />
          Penerimaan Baru
        </button>
      </div>

      {/* Receipt Form */}
      {showForm && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-red-900/30 pb-4">
            <h2 className="text-xl font-semibold text-amber-100">Form Penerimaan Piutang</h2>
            <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-white">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Customer Selection */}
            <div className="space-y-4">
              <label className="block text-sm text-gray-400">Pilih Customer</label>
              <div className="max-h-64 overflow-y-auto space-y-2">
                {customers.map(cust => (
                  <button
                    key={cust.id}
                    onClick={() => selectCustomer(cust)}
                    data-testid={`customer-${cust.id}`}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      selectedCustomer?.id === cust.id
                        ? 'bg-emerald-600/20 border-emerald-500 text-emerald-100'
                        : 'bg-[#0a0608] border-red-900/30 text-gray-300 hover:border-emerald-600/50'
                    }`}
                  >
                    <div className="font-medium">{cust.name}</div>
                    <div className="text-xs text-gray-500">{cust.code || cust.phone}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Middle: Invoice Selection */}
            <div className="space-y-4">
              <label className="block text-sm text-gray-400">Piutang Belum Lunas</label>
              {loadingInvoices ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-emerald-500" />
                </div>
              ) : invoices.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  {selectedCustomer ? 'Tidak ada piutang belum lunas' : 'Pilih customer dulu'}
                </div>
              ) : (
                <div className="max-h-64 overflow-y-auto space-y-2">
                  {invoices.map(inv => {
                    const isSelected = selectedInvoices.some(s => s.invoice_id === inv.id);
                    return (
                      <button
                        key={inv.id}
                        onClick={() => toggleInvoice(inv)}
                        data-testid={`ar-invoice-${inv.id}`}
                        className={`w-full text-left p-3 rounded-lg border transition-all ${
                          isSelected
                            ? 'bg-emerald-600/20 border-emerald-500'
                            : 'bg-[#0a0608] border-red-900/30 hover:border-emerald-600/50'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-medium text-amber-100">{inv.ar_number || inv.invoice_no}</div>
                            <div className="text-xs text-gray-500">JT: {formatDate(inv.due_date)}</div>
                          </div>
                          <div className="text-right">
                            <div className="text-emerald-400 font-mono text-sm">
                              {formatRupiah(inv.outstanding_amount || inv.amount)}
                            </div>
                            <StatusBadge status={inv.status} />
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Right: Allocation & Payment Details */}
            <div className="space-y-4">
              <label className="block text-sm text-gray-400">Detail Alokasi</label>
              
              {selectedInvoices.length === 0 ? (
                <div className="text-center py-8 text-gray-500 bg-[#0a0608] rounded-lg border border-red-900/30">
                  Pilih invoice untuk dialokasikan
                </div>
              ) : (
                <div className="space-y-3 max-h-40 overflow-y-auto">
                  {selectedInvoices.map(inv => (
                    <div key={inv.invoice_id} className="bg-[#0a0608] p-3 rounded-lg border border-red-900/30">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-amber-100">{inv.invoice_no}</span>
                        <button onClick={() => removeInvoice(inv.invoice_id)} className="text-red-400 hover:text-red-300">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                      <div className="text-xs text-gray-500 mb-2">Sisa: {formatRupiah(inv.outstanding)}</div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-[10px] text-gray-500">Terima</label>
                          <input
                            type="number"
                            value={inv.allocated_amount}
                            onChange={(e) => updateAllocation(inv.invoice_id, 'allocated_amount', e.target.value)}
                            className="w-full px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-sm text-amber-100"
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-gray-500">Diskon</label>
                          <input
                            type="number"
                            value={inv.discount_amount}
                            onChange={(e) => updateAllocation(inv.invoice_id, 'discount_amount', e.target.value)}
                            className="w-full px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-sm text-amber-100"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Receipt Details */}
              <div className="space-y-3 pt-4 border-t border-red-900/30">
                <div>
                  <label className="text-xs text-gray-400">Tanggal Terima</label>
                  <input
                    type="date"
                    value={receiptDate}
                    onChange={(e) => setReceiptDate(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Metode Pembayaran</label>
                  <select
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100"
                  >
                    <option value="transfer">Transfer Bank</option>
                    <option value="cash">Tunai</option>
                    <option value="giro">Giro/Cek</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400">Akun Kas/Bank</label>
                  <select
                    value={selectedAccount}
                    onChange={(e) => setSelectedAccount(e.target.value)}
                    data-testid="ar-account-select"
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100"
                  >
                    {cashBankAccounts.map(acc => (
                      <option key={acc.account_code} value={acc.account_code}>
                        {acc.account_code} - {acc.account_name} ({formatRupiah(acc.balance)})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400">No. Referensi</label>
                  <input
                    type="text"
                    value={referenceNo}
                    onChange={(e) => setReferenceNo(e.target.value)}
                    placeholder="No. transfer/cek"
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100"
                  />
                </div>
              </div>

              {/* Summary */}
              <div className="bg-emerald-900/20 border border-emerald-600/30 rounded-lg p-4">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400">Total Terima</span>
                  <span className="text-amber-100 font-mono">{formatRupiah(totalReceipt)}</span>
                </div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400">Total Diskon</span>
                  <span className="text-rose-400 font-mono">{formatRupiah(totalDiscount)}</span>
                </div>
                <div className="flex justify-between text-lg font-bold border-t border-emerald-600/30 pt-2">
                  <span className="text-emerald-100">GRAND TOTAL</span>
                  <span className="text-emerald-400 font-mono">{formatRupiah(totalReceipt)}</span>
                </div>
              </div>

              <button
                onClick={handleSubmit}
                disabled={submitting || selectedInvoices.length === 0}
                data-testid="submit-receipt-btn"
                className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-semibold hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {submitting ? <Loader2 className="h-5 w-5 animate-spin" /> : <CheckCircle className="h-5 w-5" />}
                Proses Penerimaan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Receipt History */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-red-900/30">
          <h3 className="text-lg font-semibold text-amber-100">Riwayat Penerimaan</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">No. Terima</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Tanggal</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Customer</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-amber-200 uppercase">Jumlah</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Metode</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Journal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {receipts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                    Belum ada penerimaan
                  </td>
                </tr>
              ) : (
                receipts.map(rec => (
                  <tr key={rec.id} className="hover:bg-red-900/10">
                    <td className="px-4 py-3 font-mono text-amber-100">{rec.receipt_no || rec.payment_no}</td>
                    <td className="px-4 py-3 text-gray-300">{formatDate(rec.receipt_date || rec.payment_date)}</td>
                    <td className="px-4 py-3 text-gray-300">{rec.customer_name}</td>
                    <td className="px-4 py-3 text-right font-mono text-emerald-400">{formatRupiah(rec.total_amount)}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                        {rec.payment_method}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-400">{rec.journal_no || rec.journal_id}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ARReceiptPage;
