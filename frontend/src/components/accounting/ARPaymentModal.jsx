import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { X, DollarSign, RefreshCw, CheckCircle, CreditCard } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

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

  // Fetch Cash/Bank accounts
  const fetchCashBankAccounts = useCallback(async () => {
    setLoadingAccounts(true);
    try {
      const res = await fetch(`${API}/api/accounts/cash-bank`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCashBankAccounts(data.accounts || []);
        // Set default account if available
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

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('id-ID', { 
      style: 'currency', 
      currency: 'IDR',
      minimumFractionDigits: 0 
    }).format(val || 0);
  };

  const handleSubmit = async () => {
    if (amount <= 0) {
      toast.error('Jumlah pembayaran harus lebih dari 0');
      return;
    }
    
    if (amount > ar.outstanding_amount) {
      toast.error('Jumlah pembayaran tidak boleh melebihi outstanding');
      return;
    }

    if (!bankAccountId) {
      toast.error('Pilih akun Kas/Bank terlebih dahulu');
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
          amount: parseFloat(amount),
          payment_method: paymentMethod,
          bank_account_id: bankAccountId,
          reference_no: referenceNo,
          notes: notes
        })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setSuccess(true);
        setResult(data);
        toast.success('Pembayaran berhasil dicatat');
      } else {
        toast.error(data.detail || 'Gagal mencatat pembayaran');
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
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg w-full max-w-md p-6 text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Pembayaran Berhasil!</h2>
          <p className="text-gray-600 mb-4">
            No. Pembayaran: <span className="font-mono font-bold">{result?.payment_no}</span>
          </p>
          <p className="text-sm text-gray-500 mb-4">
            Journal: {result?.journal_no}
          </p>
          <p className="text-gray-600 mb-6">
            Sisa Outstanding: {formatCurrency(result?.new_outstanding)}
          </p>
          <Button onClick={() => onClose(true)} className="w-full">
            Tutup
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" data-testid="ar-payment-modal">
      <div className="bg-white rounded-lg w-full max-w-lg flex flex-col max-h-[85vh]">
        {/* Header - Fixed */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-green-600 to-green-700 text-white shrink-0 rounded-t-lg">
          <div className="flex items-center gap-3">
            <DollarSign className="w-6 h-6" />
            <div>
              <h2 className="text-lg font-semibold">Pembayaran Piutang</h2>
              <p className="text-sm text-green-100">{ar.ar_no}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={() => onClose(false)} className="text-white hover:bg-green-500">
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* AR Info */}
          <Card className="bg-gray-50">
            <CardContent className="p-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Customer</p>
                  <p className="font-medium">{ar.customer_name}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Outstanding</p>
                  <p className="font-mono font-bold text-red-600">{formatCurrency(ar.outstanding_amount)}</p>
                </div>
              </div>
              {ar.source_no && (
                <div className="mt-2 pt-2 border-t">
                  <p className="text-sm text-gray-500">No. Invoice</p>
                  <p className="font-mono">{ar.source_no}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Payment Form */}
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                Jumlah Pembayaran <span className="text-red-500">*</span>
              </label>
              <Input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="Masukkan jumlah"
                className="text-lg font-mono"
                data-testid="payment-amount"
              />
              <div className="flex gap-2 mt-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setAmount(ar.outstanding_amount)}
                  data-testid="btn-pay-full"
                >
                  Bayar Penuh
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setAmount(Math.round(ar.outstanding_amount / 2))}
                >
                  50%
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setAmount(Math.round(ar.outstanding_amount / 4))}
                >
                  25%
                </Button>
              </div>
            </div>

            {/* Bank/Cash Account Selection */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                Akun Kas/Bank <span className="text-red-500">*</span>
              </label>
              {loadingAccounts ? (
                <div className="flex items-center gap-2 text-gray-500 p-3 border rounded-md bg-gray-50">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Memuat akun...</span>
                </div>
              ) : cashBankAccounts.length === 0 ? (
                <div className="p-3 border rounded-md bg-yellow-50 text-yellow-700 text-sm">
                  Tidak ada akun Kas/Bank yang aktif. Silakan tambahkan di Setting Akun.
                </div>
              ) : (
                <select
                  value={bankAccountId}
                  onChange={(e) => setBankAccountId(e.target.value)}
                  className="w-full h-10 px-3 border rounded-md"
                  data-testid="bank-account-select"
                >
                  <option value="">-- Pilih Akun Kas/Bank --</option>
                  {cashBankAccounts.map(acc => (
                    <option key={acc.id} value={acc.id}>
                      {acc.code} - {acc.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                Metode Pembayaran
              </label>
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                className="w-full h-10 px-3 border rounded-md"
                data-testid="payment-method"
              >
                <option value="cash">Cash</option>
                <option value="transfer">Transfer Bank</option>
                <option value="giro">Giro/Cek</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                No. Referensi
              </label>
              <Input
                value={referenceNo}
                onChange={(e) => setReferenceNo(e.target.value)}
                placeholder="No. bukti transfer, giro, dll"
                data-testid="payment-ref"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                Catatan
              </label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Catatan pembayaran"
                rows={2}
              />
            </div>
          </div>

          {/* Summary */}
          <Card className="border-2 border-green-200">
            <CardContent className="p-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Outstanding:</span>
                  <span className="font-mono">{formatCurrency(ar.outstanding_amount)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Pembayaran:</span>
                  <span className="font-mono text-green-600">- {formatCurrency(amount)}</span>
                </div>
                <hr />
                <div className="flex justify-between items-center">
                  <span className="font-medium text-gray-700">Sisa:</span>
                  <span className="font-mono font-bold text-lg">
                    {formatCurrency(Math.max(0, ar.outstanding_amount - amount))}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Auto Journal Info */}
          <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg">
            <p className="font-medium mb-1">Auto Journal:</p>
            <p>Dr. Kas/Bank ... Rp {formatCurrency(amount)}</p>
            <p>Cr. Piutang Usaha ... Rp {formatCurrency(amount)}</p>
          </div>
        </div>

        {/* Footer - Fixed/Sticky */}
        <div className="px-6 py-4 border-t bg-gray-50 flex justify-end gap-2 shrink-0 rounded-b-lg">
          <Button variant="outline" onClick={() => onClose(false)}>
            Batal
          </Button>
          <Button 
            onClick={handleSubmit} 
            disabled={saving || !bankAccountId}
            className="bg-green-600 hover:bg-green-700"
            data-testid="btn-submit-payment"
          >
            {saving ? (
              <RefreshCw className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <DollarSign className="w-4 h-4 mr-2" />
            )}
            Catat Pembayaran
          </Button>
        </div>
      </div>
    </div>
  );
}
