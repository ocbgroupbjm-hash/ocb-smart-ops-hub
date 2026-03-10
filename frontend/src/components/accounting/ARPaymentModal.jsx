import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { X, DollarSign, CreditCard, RefreshCw, CheckCircle } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function ARPaymentModal({ ar, onClose }) {
  const [amount, setAmount] = useState(ar.outstanding_amount || 0);
  const [paymentMethod, setPaymentMethod] = useState('transfer');
  const [referenceNo, setReferenceNo] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState(null);
  
  const token = localStorage.getItem('token');

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('id-ID', { 
      style: 'currency', 
      currency: 'IDR',
      minimumFractionDigits: 0 
    }).format(val || 0);
  };

  const handleSubmit = async () => {
    if (amount <= 0) {
      alert('Jumlah pembayaran harus lebih dari 0');
      return;
    }
    
    if (amount > ar.outstanding_amount) {
      alert('Jumlah pembayaran tidak boleh melebihi outstanding');
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
          reference_no: referenceNo,
          notes: notes
        })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setSuccess(true);
        setResult(data);
      } else {
        alert(data.detail || 'Gagal mencatat pembayaran');
      }
    } catch (err) {
      console.error('Error recording payment:', err);
      alert('Terjadi kesalahan');
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
      <div className="bg-white rounded-lg w-full max-w-lg overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-green-600 to-green-700 text-white">
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

        {/* Content */}
        <div className="p-6 space-y-6">
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
                >
                  Bayar Penuh
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setAmount(ar.outstanding_amount / 2)}
                >
                  50%
                </Button>
              </div>
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
                <option value="bank">Bank</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                No. Referensi
              </label>
              <Input
                value={referenceNo}
                onChange={(e) => setReferenceNo(e.target.value)}
                placeholder="No. bukti transfer, dll"
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
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Setelah pembayaran:</span>
                <span className="font-mono font-bold text-lg">
                  {formatCurrency(ar.outstanding_amount - amount)}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50 flex justify-end gap-2">
          <Button variant="outline" onClick={() => onClose(false)}>
            Batal
          </Button>
          <Button 
            onClick={handleSubmit} 
            disabled={saving}
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
