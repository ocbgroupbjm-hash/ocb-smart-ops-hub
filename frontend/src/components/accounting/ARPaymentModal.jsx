import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { X, DollarSign, RefreshCw, CheckCircle, CreditCard, Wallet, User } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

// OCB TITAN Design Tokens - Dark Enterprise Theme
const DESIGN = {
  text: {
    primary: 'text-[#E5E7EB]',
    secondary: 'text-[#9CA3AF]',
    accent: 'text-[#F97316]',
  },
  bg: {
    modal: 'bg-[#1E293B]',
    card: 'bg-[#0F172A]',
    input: 'bg-[#0F172A]',
  },
  border: {
    default: 'border-[#334155]',
  }
};

export default function ARPaymentModal({ ar, onClose }) {
  const [amount, setAmount] = useState(ar.outstanding_amount || 0);
  const [paymentMethod, setPaymentMethod] = useState('transfer');
  const [bankAccountId, setBankAccountId] = useState('');
  const [referenceNo, setReferenceNo] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState(null);
  const [cashBankAccounts, setCashBankAccounts] = useState([]);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  
  const token = localStorage.getItem('token');

  const fetchCashBankAccounts = useCallback(async () => {
    setLoadingAccounts(true);
    try {
      const res = await fetch(`${API}/api/accounts/cash-bank`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCashBankAccounts(data.accounts || []);
        if (data.accounts?.length > 0) {
          setBankAccountId(data.accounts[0].id);
        }
      }
    } catch (err) {
      console.error('Error fetching accounts:', err);
    } finally {
      setLoadingAccounts(false);
    }
  }, [token]);

  useEffect(() => {
    fetchCashBankAccounts();
  }, [fetchCashBankAccounts]);

  const formatCurrency = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (amount <= 0) {
      toast.error('Masukkan jumlah pembayaran');
      return;
    }
    
    if (amount > ar.outstanding_amount) {
      toast.error('Jumlah pembayaran melebihi outstanding');
      return;
    }
    
    setSaving(true);
    try {
      const res = await fetch(`${API}/api/ar/${ar.id}/payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          amount,
          payment_method: paymentMethod,
          bank_account_id: bankAccountId,
          reference_no: referenceNo,
          notes
        })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setResult(data);
        setSuccess(true);
        toast.success('Pembayaran berhasil dicatat');
      } else {
        toast.error(data.detail || 'Gagal menyimpan pembayaran');
      }
    } catch (err) {
      console.error('Error recording payment:', err);
      toast.error('Terjadi kesalahan');
    } finally {
      setSaving(false);
    }
  };

  if (success) {
    return (
      <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
        <div className={`${DESIGN.bg.modal} ${DESIGN.border.default} border rounded-xl w-full max-w-md p-6 text-center shadow-2xl`}>
          <CheckCircle className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
          <h2 className={`text-xl font-bold ${DESIGN.text.primary} mb-2`}>Pembayaran Berhasil!</h2>
          <p className={`${DESIGN.text.secondary} mb-4`}>
            No. Pembayaran: <span className={`font-mono font-bold ${DESIGN.text.accent}`}>{result?.payment_no}</span>
          </p>
          <p className={`text-sm ${DESIGN.text.secondary} mb-4`}>
            Journal: <span className="font-mono">{result?.journal_no}</span>
          </p>
          <p className={`${DESIGN.text.primary} mb-6`}>
            Sisa Outstanding: <span className="text-emerald-400 font-bold">{formatCurrency(result?.new_outstanding)}</span>
          </p>
          <Button 
            onClick={() => onClose(true)} 
            className="w-full bg-[#F97316] hover:bg-[#EA580C] text-white"
          >
            Tutup
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" data-testid="ar-payment-modal">
      <div className={`${DESIGN.bg.modal} ${DESIGN.border.default} border rounded-xl w-full max-w-lg flex flex-col max-h-[85vh] shadow-2xl`}>
        {/* Header */}
        <div className={`flex items-center justify-between px-6 py-4 border-b ${DESIGN.border.default} bg-gradient-to-r from-emerald-600 to-emerald-700 text-white shrink-0 rounded-t-xl`}>
          <div className="flex items-center gap-3">
            <DollarSign className="w-6 h-6" />
            <div>
              <h2 className="text-lg font-semibold">Terima Pembayaran</h2>
              <p className="text-sm text-emerald-100">{ar.ar_no}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={() => onClose(false)} className="text-white hover:bg-emerald-600/50">
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* AR Info Card */}
          <div className={`${DESIGN.bg.card} ${DESIGN.border.default} border rounded-lg p-4`}>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className={`text-sm ${DESIGN.text.secondary}`}>Customer</p>
                <p className={`font-medium ${DESIGN.text.primary} flex items-center gap-2`}>
                  <User className="w-4 h-4 text-[#9CA3AF]" />
                  {ar.customer_name}
                </p>
              </div>
              <div className="text-right">
                <p className={`text-sm ${DESIGN.text.secondary}`}>Outstanding</p>
                <p className="font-mono font-bold text-emerald-400">{formatCurrency(ar.outstanding_amount)}</p>
              </div>
            </div>
            {ar.invoice_no && (
              <div className={`mt-3 pt-3 border-t ${DESIGN.border.default}`}>
                <p className={`text-sm ${DESIGN.text.secondary}`}>No. Invoice</p>
                <p className={`font-mono ${DESIGN.text.primary}`}>{ar.invoice_no}</p>
              </div>
            )}
          </div>

          {/* Payment Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className={`text-sm font-medium ${DESIGN.text.secondary} mb-1 block`}>
                Jumlah Pembayaran <span className="text-rose-400">*</span>
              </label>
              <Input
                type="number"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                max={ar.outstanding_amount}
                min={0}
                className={`${DESIGN.bg.input} ${DESIGN.border.default} ${DESIGN.text.primary}`}
                data-testid="payment-amount"
              />
              <div className="flex justify-between mt-1">
                <span className={`text-xs ${DESIGN.text.secondary}`}>Max: {formatCurrency(ar.outstanding_amount)}</span>
                <button
                  type="button"
                  onClick={() => setAmount(ar.outstanding_amount)}
                  className={`text-xs ${DESIGN.text.accent} hover:underline`}
                >
                  Bayar Penuh
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={`text-sm font-medium ${DESIGN.text.secondary} mb-1 block`}>
                  Metode Pembayaran
                </label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className={`w-full px-3 py-2 rounded-md ${DESIGN.bg.input} ${DESIGN.border.default} border ${DESIGN.text.primary}`}
                >
                  <option value="transfer">Transfer Bank</option>
                  <option value="cash">Tunai</option>
                  <option value="giro">Giro</option>
                </select>
              </div>
              <div>
                <label className={`text-sm font-medium ${DESIGN.text.secondary} mb-1 block`}>
                  Akun Kas/Bank
                </label>
                {loadingAccounts ? (
                  <div className={`flex items-center gap-2 ${DESIGN.text.secondary} p-3 border rounded-md ${DESIGN.bg.input} ${DESIGN.border.default}`}>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Loading...</span>
                  </div>
                ) : cashBankAccounts.length === 0 ? (
                  <div className={`flex items-center gap-2 text-amber-400 p-3 border rounded-md bg-amber-500/10 border-amber-500/30`}>
                    <Wallet className="w-4 h-4" />
                    <span className="text-sm">Tidak ada akun</span>
                  </div>
                ) : (
                  <select
                    value={bankAccountId}
                    onChange={(e) => setBankAccountId(e.target.value)}
                    className={`w-full px-3 py-2 rounded-md ${DESIGN.bg.input} ${DESIGN.border.default} border ${DESIGN.text.primary}`}
                  >
                    {cashBankAccounts.map(acc => (
                      <option key={acc.id} value={acc.id}>
                        {acc.code} - {acc.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            <div>
              <label className={`text-sm font-medium ${DESIGN.text.secondary} mb-1 block`}>
                No. Referensi
              </label>
              <Input
                type="text"
                value={referenceNo}
                onChange={(e) => setReferenceNo(e.target.value)}
                placeholder="No. bukti transfer / cek"
                className={`${DESIGN.bg.input} ${DESIGN.border.default} ${DESIGN.text.primary} placeholder:text-[#64748B]`}
              />
            </div>

            <div>
              <label className={`text-sm font-medium ${DESIGN.text.secondary} mb-1 block`}>
                Catatan
              </label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder="Catatan pembayaran (opsional)"
                className={`${DESIGN.bg.input} ${DESIGN.border.default} ${DESIGN.text.primary} placeholder:text-[#64748B]`}
              />
            </div>
          </form>

          {/* Journal Preview */}
          <div className={`text-xs ${DESIGN.text.secondary} ${DESIGN.bg.card} ${DESIGN.border.default} border p-3 rounded-lg`}>
            <p className="font-medium mb-2">Preview Jurnal:</p>
            <div className="space-y-1 font-mono">
              <p>Dr. {paymentMethod === 'cash' ? 'Kas' : 'Bank'} ... {formatCurrency(amount)}</p>
              <p>Cr. Piutang Usaha ... {formatCurrency(amount)}</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className={`px-6 py-4 border-t ${DESIGN.border.default} ${DESIGN.bg.card} flex justify-end gap-2 shrink-0 rounded-b-xl`}>
          <Button
            variant="outline"
            onClick={() => onClose(false)}
            className={`${DESIGN.border.default} ${DESIGN.text.primary} hover:bg-[#334155]`}
          >
            Batal
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={saving || loadingAccounts || amount <= 0}
            className="bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-50"
          >
            {saving ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Menyimpan...
              </>
            ) : (
              <>
                <DollarSign className="w-4 h-4 mr-2" />
                Terima {formatCurrency(amount)}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
