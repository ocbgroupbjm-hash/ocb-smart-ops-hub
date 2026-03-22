import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  DollarSign, Search, Loader2, X, Building2, Plus, ChevronRight, 
  AlertTriangle, CheckCircle, Receipt, CreditCard, Wallet, Calendar,
  ArrowDownRight, Trash2
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

const APPaymentPage = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [suppliers, setSuppliers] = useState([]);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loadingInvoices, setLoadingInvoices] = useState(false);
  const [cashBankAccounts, setCashBankAccounts] = useState([]);
  const [payments, setPayments] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  // Form state
  const [selectedInvoices, setSelectedInvoices] = useState([]);
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().split('T')[0]);
  const [paymentMethod, setPaymentMethod] = useState('transfer');
  const [selectedAccount, setSelectedAccount] = useState('');
  const [referenceNo, setReferenceNo] = useState('');
  const [notes, setNotes] = useState('');

  // Load suppliers on mount
  useEffect(() => {
    loadSuppliers();
    loadCashBankAccounts();
    loadPayments();
  }, []);

  const loadSuppliers = async () => {
    try {
      const res = await api('/api/suppliers?limit=500');
      if (res.ok) {
        const data = await res.json();
        setSuppliers(data.items || data || []);
      }
    } catch (err) {
      console.error('Load suppliers error:', err);
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
        // Auto-select first account
        if (data.accounts?.length > 0) {
          setSelectedAccount(data.accounts[0].account_code);
        }
      }
    } catch (err) {
      console.error('Load accounts error:', err);
    }
  };

  const loadPayments = async () => {
    try {
      const res = await api('/api/ap/payments?limit=50');
      if (res.ok) {
        const data = await res.json();
        setPayments(data.items || data || []);
      }
    } catch (err) {
      console.error('Load payments error:', err);
    }
  };

  const loadSupplierInvoices = async (supplierId) => {
    setLoadingInvoices(true);
    try {
      const res = await api(`/api/payment-allocation/ap/supplier/${supplierId}/unpaid`);
      if (res.ok) {
        const data = await res.json();
        setInvoices(data.invoices || []);
      }
    } catch (err) {
      toast.error('Gagal memuat invoice');
    } finally {
      setLoadingInvoices(false);
    }
  };

  const selectSupplier = (supplier) => {
    setSelectedSupplier(supplier);
    setSelectedInvoices([]);
    loadSupplierInvoices(supplier.id);
  };

  const toggleInvoice = (invoice) => {
    const exists = selectedInvoices.find(i => i.invoice_id === invoice.id);
    if (exists) {
      setSelectedInvoices(selectedInvoices.filter(i => i.invoice_id !== invoice.id));
    } else {
      setSelectedInvoices([...selectedInvoices, {
        invoice_id: invoice.id,
        invoice_no: invoice.ap_number || invoice.invoice_no,
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
          toast.error('Alokasi tidak boleh melebihi sisa hutang');
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

  const totalPayment = selectedInvoices.reduce((sum, inv) => sum + inv.allocated_amount, 0);
  const totalDiscount = selectedInvoices.reduce((sum, inv) => sum + inv.discount_amount, 0);

  const handleSubmit = async () => {
    if (!selectedSupplier) {
      toast.error('Pilih supplier terlebih dahulu');
      return;
    }
    if (selectedInvoices.length === 0) {
      toast.error('Pilih minimal 1 invoice untuk dibayar');
      return;
    }
    if (!selectedAccount) {
      toast.error('Pilih akun kas/bank untuk pembayaran');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        supplier_id: selectedSupplier.id,
        payment_date: paymentDate,
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

      const res = await api('/api/cashflow/ap-payment/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const result = await res.json();
        toast.success(`Pembayaran ${result.payment_no} berhasil dibuat`);
        // Reset form
        setSelectedInvoices([]);
        setReferenceNo('');
        setNotes('');
        setShowForm(false);
        loadPayments();
        if (selectedSupplier) {
          loadSupplierInvoices(selectedSupplier.id);
        }
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal membuat pembayaran');
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
          <h1 className="text-2xl font-bold text-amber-100" data-testid="page-title">Pembayaran Hutang</h1>
          <p className="text-gray-400">Kelola pembayaran hutang ke supplier</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          data-testid="new-payment-btn"
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg hover:from-red-500 hover:to-amber-500"
        >
          <Plus className="h-5 w-5" />
          Pembayaran Baru
        </button>
      </div>

      {/* Payment Form */}
      {showForm && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-red-900/30 pb-4">
            <h2 className="text-xl font-semibold text-amber-100">Form Pembayaran Hutang</h2>
            <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-white">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Supplier Selection */}
            <div className="space-y-4">
              <label className="block text-sm text-gray-400">Pilih Supplier</label>
              <div className="max-h-64 overflow-y-auto space-y-2">
                {suppliers.map(sup => (
                  <button
                    key={sup.id}
                    onClick={() => selectSupplier(sup)}
                    data-testid={`supplier-${sup.id}`}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      selectedSupplier?.id === sup.id
                        ? 'bg-amber-600/20 border-amber-500 text-amber-100'
                        : 'bg-[#0a0608] border-red-900/30 text-gray-300 hover:border-amber-600/50'
                    }`}
                  >
                    <div className="font-medium">{sup.name}</div>
                    <div className="text-xs text-gray-500">{sup.code || sup.phone}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Middle: Invoice Selection */}
            <div className="space-y-4">
              <label className="block text-sm text-gray-400">Invoice Belum Lunas</label>
              {loadingInvoices ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-amber-500" />
                </div>
              ) : invoices.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  {selectedSupplier ? 'Tidak ada invoice belum lunas' : 'Pilih supplier dulu'}
                </div>
              ) : (
                <div className="max-h-64 overflow-y-auto space-y-2">
                  {invoices.map(inv => {
                    const isSelected = selectedInvoices.some(s => s.invoice_id === inv.id);
                    return (
                      <button
                        key={inv.id}
                        onClick={() => toggleInvoice(inv)}
                        data-testid={`invoice-${inv.id}`}
                        className={`w-full text-left p-3 rounded-lg border transition-all ${
                          isSelected
                            ? 'bg-emerald-600/20 border-emerald-500'
                            : 'bg-[#0a0608] border-red-900/30 hover:border-amber-600/50'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-medium text-amber-100">{inv.ap_number || inv.invoice_no}</div>
                            <div className="text-xs text-gray-500">JT: {formatDate(inv.due_date)}</div>
                          </div>
                          <div className="text-right">
                            <div className="text-amber-400 font-mono text-sm">
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
                          <label className="text-[10px] text-gray-500">Bayar</label>
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

              {/* Payment Details */}
              <div className="space-y-3 pt-4 border-t border-red-900/30">
                <div>
                  <label className="text-xs text-gray-400">Tanggal Bayar</label>
                  <input
                    type="date"
                    value={paymentDate}
                    onChange={(e) => setPaymentDate(e.target.value)}
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
                    data-testid="account-select"
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
              <div className="bg-amber-900/20 border border-amber-600/30 rounded-lg p-4">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400">Total Bayar</span>
                  <span className="text-amber-100 font-mono">{formatRupiah(totalPayment)}</span>
                </div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400">Total Diskon</span>
                  <span className="text-emerald-400 font-mono">{formatRupiah(totalDiscount)}</span>
                </div>
                <div className="flex justify-between text-lg font-bold border-t border-amber-600/30 pt-2">
                  <span className="text-amber-100">GRAND TOTAL</span>
                  <span className="text-amber-400 font-mono">{formatRupiah(totalPayment)}</span>
                </div>
              </div>

              <button
                onClick={handleSubmit}
                disabled={submitting || selectedInvoices.length === 0}
                data-testid="submit-payment-btn"
                className="w-full py-3 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg font-semibold hover:from-red-500 hover:to-amber-500 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {submitting ? <Loader2 className="h-5 w-5 animate-spin" /> : <CheckCircle className="h-5 w-5" />}
                Proses Pembayaran
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payment History */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-red-900/30">
          <h3 className="text-lg font-semibold text-amber-100">Riwayat Pembayaran</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">No. Bayar</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Tanggal</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Supplier</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-amber-200 uppercase">Jumlah</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Metode</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-amber-200 uppercase">Journal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {payments.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                    Belum ada pembayaran
                  </td>
                </tr>
              ) : (
                payments.map(pay => (
                  <tr key={pay.id} className="hover:bg-red-900/10">
                    <td className="px-4 py-3 font-mono text-amber-100">{pay.payment_no}</td>
                    <td className="px-4 py-3 text-gray-300">{formatDate(pay.payment_date)}</td>
                    <td className="px-4 py-3 text-gray-300">{pay.supplier_name}</td>
                    <td className="px-4 py-3 text-right font-mono text-amber-400">{formatRupiah(pay.total_amount)}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                        {pay.payment_method}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-400">{pay.journal_no || pay.journal_id}</td>
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

export default APPaymentPage;
