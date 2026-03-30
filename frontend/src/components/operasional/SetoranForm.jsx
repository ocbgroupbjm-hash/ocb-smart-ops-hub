import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Textarea } from '../ui/textarea';
import {
  X, Save, Send, CheckCircle, XCircle, FileText, AlertTriangle,
  RefreshCw, Calendar, Wallet, Building2, User, Clock, Receipt,
  Calculator, ArrowRight, Ban, Lock, Printer, BookOpen
} from 'lucide-react';

import { getApiUrl } from '../../utils/apiConfig';
const API = getApiUrl();

const STATUS_CONFIG = {
  draft: { label: 'Draft', color: 'bg-blue-100 text-blue-800', icon: FileText },
  pending: { label: 'Menunggu Setor', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  received: { label: 'Diterima', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  verified: { label: 'Diverifikasi', color: 'bg-emerald-100 text-emerald-800', icon: CheckCircle },
  approved: { label: 'Approved', color: 'bg-teal-100 text-teal-800', icon: CheckCircle },
  posted: { label: 'Posted', color: 'bg-purple-100 text-purple-800', icon: FileText },
  rejected: { label: 'Ditolak', color: 'bg-red-100 text-red-800', icon: XCircle },
  cancelled: { label: 'Dibatalkan', color: 'bg-gray-100 text-gray-800', icon: XCircle }
};

export default function SetoranForm({ isOpen, onClose, deposit, mode }) {
  const [activeTab, setActiveTab] = useState('summary');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [salesData, setSalesData] = useState(null);
  const [depositData, setDepositData] = useState(null);
  const [transactions, setTransactions] = useState([]);
  
  // Form fields (only editable ones)
  const [salesDate, setSalesDate] = useState(new Date().toISOString().split('T')[0]);
  const [cashReceived, setCashReceived] = useState(0);
  const [differenceReason, setDifferenceReason] = useState('');
  const [notes, setNotes] = useState('');
  
  const token = localStorage.getItem('token');
  const isCreate = mode === 'create';
  const isEdit = mode === 'edit';
  const isView = mode === 'view';
  const canEdit = isCreate || (isEdit && ['draft', 'pending'].includes(deposit?.status));

  // Fetch sales data for new deposit
  const fetchSalesForDeposit = useCallback(async () => {
    if (!isCreate) return;
    
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/deposit/my-sales?sales_date=${salesDate}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      
      if (res.ok) {
        setSalesData(data);
        setTransactions(data.summary?.transactions || []);
      } else {
        alert(data.detail || 'Gagal mengambil data penjualan');
      }
    } catch (err) {
      console.error('Error fetching sales:', err);
    } finally {
      setLoading(false);
    }
  }, [token, salesDate, isCreate]);

  // Fetch deposit detail for view/edit
  const fetchDepositDetail = useCallback(async () => {
    if (isCreate || !deposit?.id) return;
    
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/deposit/${deposit.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      
      if (res.ok) {
        setDepositData(data);
        setTransactions(data.transactions || []);
        setCashReceived(data.cash_received || 0);
        setDifferenceReason(data.difference_reason || '');
        setNotes(data.notes || '');
      }
    } catch (err) {
      console.error('Error fetching deposit:', err);
    } finally {
      setLoading(false);
    }
  }, [token, deposit, isCreate]);

  useEffect(() => {
    if (isOpen) {
      if (isCreate) {
        fetchSalesForDeposit();
      } else {
        fetchDepositDetail();
      }
    }
  }, [isOpen, isCreate, fetchSalesForDeposit, fetchDepositDetail]);

  // Calculate difference
  const cashShouldDeposit = isCreate 
    ? (salesData?.summary?.cash_should_deposit || 0)
    : (depositData?.cash_should_deposit || 0);
  
  const difference = cashReceived - cashShouldDeposit;
  const differenceStatus = Math.abs(difference) < 0.01 ? 'match' : (difference < 0 ? 'short' : 'over');

  // Create new deposit
  const handleCreate = async () => {
    if (!salesData?.summary?.total_transactions) {
      alert('Tidak ada transaksi untuk disetor');
      return;
    }
    
    setSaving(true);
    try {
      const res = await fetch(`${API}/api/deposit/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          sales_date: salesDate,
          shift_id: '',
          notes: notes
        })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        alert(`Setoran ${data.deposit_number} berhasil dibuat`);
        onClose(true);
      } else {
        alert(data.detail || 'Gagal membuat setoran');
      }
    } catch (err) {
      console.error('Error creating deposit:', err);
      alert('Terjadi kesalahan');
    } finally {
      setSaving(false);
    }
  };

  // Update deposit
  const handleUpdate = async () => {
    // Validate difference reason
    if (differenceStatus !== 'match' && !differenceReason.trim()) {
      alert('Alasan selisih WAJIB diisi karena ada selisih');
      return;
    }
    
    setSaving(true);
    try {
      const res = await fetch(`${API}/api/deposit/${deposit.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          cash_received: cashReceived,
          difference_reason: differenceReason,
          admin_fee: 0,
          notes: notes
        })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        alert('Setoran berhasil diupdate');
        onClose(true);
      } else {
        alert(data.detail || 'Gagal update setoran');
      }
    } catch (err) {
      console.error('Error updating deposit:', err);
      alert('Terjadi kesalahan');
    } finally {
      setSaving(false);
    }
  };

  // Action handlers
  const handleAction = async (action) => {
    const confirmMsg = {
      receive: 'Konfirmasi terima setoran ini?',
      verify: 'Konfirmasi verifikasi setoran ini?',
      approve: 'Konfirmasi approve setoran ini?',
      post: 'Posting setoran ke jurnal akuntansi?',
      cancel: 'Batalkan setoran ini?'
    };
    
    if (!window.confirm(confirmMsg[action])) return;
    
    setSaving(true);
    try {
      let url = `${API}/api/deposit/${deposit.id}/${action}`;
      let body = {};
      
      if (action === 'verify') body = { verified: true, notes: '' };
      if (action === 'approve') body = { approved: true, notes: '' };
      if (action === 'cancel') url += `?reason=${encodeURIComponent('Dibatalkan user')}`;
      
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        alert(data.message || 'Berhasil');
        onClose(true);
      } else {
        alert(data.detail || 'Gagal');
      }
    } catch (err) {
      console.error('Error:', err);
      alert('Terjadi kesalahan');
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('id-ID', { 
      style: 'currency', 
      currency: 'IDR',
      minimumFractionDigits: 0 
    }).format(val || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('id-ID', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    });
  };

  if (!isOpen) return null;

  const currentData = isCreate ? salesData : depositData;
  const statusCfg = STATUS_CONFIG[depositData?.status] || STATUS_CONFIG.draft;
  const StatusIcon = statusCfg.icon;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" data-testid="setoran-form-modal">
      <div className="bg-white rounded-lg w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white">
          <div className="flex items-center gap-3">
            <Wallet className="w-6 h-6" />
            <div>
              <h2 className="text-lg font-semibold">
                {isCreate ? 'Buat Setoran Baru' : `Setoran ${depositData?.deposit_number || ''}`}
              </h2>
              {!isCreate && depositData && (
                <div className="flex items-center gap-2 text-sm text-blue-100">
                  <Badge className={`${statusCfg.color} text-xs`}>
                    <StatusIcon className="w-3 h-3 mr-1" />
                    {statusCfg.label}
                  </Badge>
                </div>
              )}
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={() => onClose(false)} className="text-white hover:bg-blue-500">
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Tabs */}
        <div className="flex border-b bg-gray-50">
          {['summary', 'transactions', 'difference', 'journal'].map((tab) => (
            <button
              key={tab}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-blue-600 text-blue-600 bg-white'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab(tab)}
              data-testid={`tab-${tab}`}
            >
              {tab === 'summary' && 'Ringkasan'}
              {tab === 'transactions' && 'Transaksi'}
              {tab === 'difference' && 'Selisih'}
              {tab === 'journal' && 'Jurnal'}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">Memuat data...</span>
            </div>
          ) : (
            <>
              {/* Summary Tab */}
              {activeTab === 'summary' && (
                <div className="space-y-6">
                  {/* Date selector for create */}
                  {isCreate && (
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-end gap-4">
                          <div className="flex-1">
                            <label className="text-sm font-medium text-gray-700 mb-1 block">
                              Tanggal Penjualan <span className="text-red-500">*</span>
                            </label>
                            <Input
                              type="date"
                              value={salesDate}
                              onChange={(e) => setSalesDate(e.target.value)}
                              className="max-w-xs"
                              data-testid="sales-date-input"
                            />
                          </div>
                          <Button onClick={fetchSalesForDeposit} variant="outline">
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Ambil Data Penjualan
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Info Cards */}
                  <div className="grid grid-cols-2 gap-4">
                    {/* Branch & Cashier Info - READ ONLY */}
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-gray-500 flex items-center gap-2">
                          <Building2 className="w-4 h-4" />
                          Informasi Cabang & Kasir
                          <Lock className="w-3 h-3 text-gray-400" />
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div>
                          <label className="text-xs text-gray-500">Cabang</label>
                          <p className="font-medium">{currentData?.branch_name || '-'}</p>
                        </div>
                        <div>
                          <label className="text-xs text-gray-500">Kasir</label>
                          <p className="font-medium">{currentData?.cashier_name || '-'}</p>
                        </div>
                        <div>
                          <label className="text-xs text-gray-500">Tanggal Penjualan</label>
                          <p className="font-medium">{formatDate(currentData?.sales_date || salesDate)}</p>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Sales Summary - READ ONLY */}
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-gray-500 flex items-center gap-2">
                          <Receipt className="w-4 h-4" />
                          Ringkasan Penjualan
                          <Lock className="w-3 h-3 text-gray-400" />
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Jumlah Transaksi</span>
                          <span className="font-medium">
                            {isCreate ? salesData?.summary?.total_transactions : depositData?.total_transactions} transaksi
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Total Penjualan Kotor</span>
                          <span className="font-mono">
                            {formatCurrency(isCreate ? salesData?.summary?.gross_sales : depositData?.gross_sales)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Diskon</span>
                          <span className="font-mono text-red-600">
                            -{formatCurrency(isCreate ? salesData?.summary?.total_discount : depositData?.total_discount)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Pajak</span>
                          <span className="font-mono">
                            {formatCurrency(isCreate ? salesData?.summary?.total_tax : depositData?.total_tax)}
                          </span>
                        </div>
                        <div className="flex justify-between border-t pt-2">
                          <span className="font-medium">Total Penjualan Bersih</span>
                          <span className="font-mono font-bold">
                            {formatCurrency(isCreate ? salesData?.summary?.net_sales : depositData?.net_sales)}
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Payment Breakdown - READ ONLY */}
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-500 flex items-center gap-2">
                        <Wallet className="w-4 h-4" />
                        Rincian Pembayaran
                        <Lock className="w-3 h-3 text-gray-400" />
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-4 gap-4">
                        <div className="text-center p-3 bg-green-50 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1">Cash Diterima</p>
                          <p className="font-mono font-bold text-green-700">
                            {formatCurrency(isCreate ? salesData?.summary?.cash_received : depositData?.cash_received_sales)}
                          </p>
                        </div>
                        <div className="text-center p-3 bg-orange-50 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1">Kembalian</p>
                          <p className="font-mono font-bold text-orange-700">
                            {formatCurrency(isCreate ? salesData?.summary?.cash_change : depositData?.cash_change)}
                          </p>
                        </div>
                        <div className="text-center p-3 bg-blue-50 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1">Transfer</p>
                          <p className="font-mono font-bold text-blue-700">
                            {formatCurrency(isCreate ? salesData?.summary?.transfer_amount : depositData?.transfer_amount)}
                          </p>
                        </div>
                        <div className="text-center p-3 bg-purple-50 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1">QRIS/E-Wallet</p>
                          <p className="font-mono font-bold text-purple-700">
                            {formatCurrency(
                              (isCreate ? salesData?.summary?.qris_amount : depositData?.qris_amount || 0) +
                              (isCreate ? salesData?.summary?.ewallet_amount : depositData?.ewallet_amount || 0)
                            )}
                          </p>
                        </div>
                      </div>
                      
                      <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="text-sm text-gray-600">Cash yang Harus Disetor</p>
                            <p className="text-xs text-gray-400">(Cash Diterima - Kembalian)</p>
                          </div>
                          <p className="text-2xl font-mono font-bold text-blue-700">
                            {formatCurrency(cashShouldDeposit)}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Cash Received Input - EDITABLE */}
                  {!isCreate && canEdit && (
                    <Card className="border-2 border-blue-200">
                      <CardHeader className="pb-2 bg-blue-50">
                        <CardTitle className="text-sm text-blue-700 flex items-center gap-2">
                          <Calculator className="w-4 h-4" />
                          Input Nominal Fisik
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-4">
                        <div className="space-y-4">
                          <div>
                            <label className="text-sm font-medium text-gray-700 mb-1 block">
                              Cash Fisik Diterima <span className="text-red-500">*</span>
                            </label>
                            <Input
                              type="number"
                              value={cashReceived}
                              onChange={(e) => setCashReceived(parseFloat(e.target.value) || 0)}
                              placeholder="Masukkan nominal cash fisik"
                              className="max-w-xs text-lg font-mono"
                              data-testid="cash-received-input"
                            />
                          </div>
                          
                          {/* Difference Display */}
                          <div className={`p-4 rounded-lg ${
                            differenceStatus === 'match' ? 'bg-green-50 border border-green-200' :
                            differenceStatus === 'short' ? 'bg-red-50 border border-red-200' :
                            'bg-yellow-50 border border-yellow-200'
                          }`}>
                            <div className="flex justify-between items-center">
                              <div>
                                <p className="font-medium">
                                  {differenceStatus === 'match' ? 'SESUAI' :
                                   differenceStatus === 'short' ? 'SELISIH KURANG' : 'SELISIH LEBIH'}
                                </p>
                                <p className="text-sm text-gray-500">
                                  {formatCurrency(cashReceived)} - {formatCurrency(cashShouldDeposit)}
                                </p>
                              </div>
                              <p className={`text-2xl font-mono font-bold ${
                                differenceStatus === 'match' ? 'text-green-700' :
                                differenceStatus === 'short' ? 'text-red-700' : 'text-yellow-700'
                              }`}>
                                {formatCurrency(difference)}
                              </p>
                            </div>
                          </div>

                          {/* Difference Reason - Required if not match */}
                          {differenceStatus !== 'match' && (
                            <div>
                              <label className="text-sm font-medium text-red-700 mb-1 block">
                                Alasan Selisih <span className="text-red-500">* WAJIB DIISI</span>
                              </label>
                              <Textarea
                                value={differenceReason}
                                onChange={(e) => setDifferenceReason(e.target.value)}
                                placeholder="Jelaskan alasan selisih..."
                                className="border-red-200"
                                rows={3}
                                data-testid="difference-reason-input"
                              />
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Notes */}
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-500">Catatan</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {canEdit ? (
                        <Textarea
                          value={notes}
                          onChange={(e) => setNotes(e.target.value)}
                          placeholder="Catatan tambahan (opsional)"
                          rows={2}
                          data-testid="notes-input"
                        />
                      ) : (
                        <p className="text-gray-600">{depositData?.notes || '-'}</p>
                      )}
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Transactions Tab */}
              {activeTab === 'transactions' && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Receipt className="w-5 h-5" />
                      Daftar Transaksi ({transactions.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {transactions.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        Tidak ada transaksi
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-3 py-2 text-left">No. Transaksi</th>
                              <th className="px-3 py-2 text-left">Waktu</th>
                              <th className="px-3 py-2 text-left">Pelanggan</th>
                              <th className="px-3 py-2 text-right">Gross</th>
                              <th className="px-3 py-2 text-right">Net</th>
                              <th className="px-3 py-2 text-right">Cash</th>
                              <th className="px-3 py-2 text-right">Kembalian</th>
                              <th className="px-3 py-2 text-center">Status</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {transactions.map((trx, idx) => (
                              <tr key={idx} className={trx.is_void ? 'bg-red-50' : 'hover:bg-gray-50'}>
                                <td className="px-3 py-2 font-mono text-xs">
                                  {trx.transaction_number}
                                </td>
                                <td className="px-3 py-2 text-xs">
                                  {trx.transaction_time || '-'}
                                </td>
                                <td className="px-3 py-2">
                                  {trx.customer_name || '-'}
                                </td>
                                <td className="px-3 py-2 text-right font-mono">
                                  {formatCurrency(trx.gross_amount)}
                                </td>
                                <td className="px-3 py-2 text-right font-mono font-medium">
                                  {formatCurrency(trx.net_amount)}
                                </td>
                                <td className="px-3 py-2 text-right font-mono text-green-600">
                                  {formatCurrency(trx.cash)}
                                </td>
                                <td className="px-3 py-2 text-right font-mono text-orange-600">
                                  {formatCurrency(trx.change)}
                                </td>
                                <td className="px-3 py-2 text-center">
                                  {trx.is_void ? (
                                    <Badge className="bg-red-100 text-red-800 text-xs">VOID</Badge>
                                  ) : (
                                    <Badge className="bg-green-100 text-green-800 text-xs">OK</Badge>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Difference Tab */}
              {activeTab === 'difference' && (
                <div className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5" />
                        Analisis Selisih
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4 mb-6">
                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                          <p className="text-sm text-gray-500 mb-1">Seharusnya Disetor</p>
                          <p className="text-xl font-mono font-bold text-blue-700">
                            {formatCurrency(cashShouldDeposit)}
                          </p>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                          <p className="text-sm text-gray-500 mb-1">Cash Diterima</p>
                          <p className="text-xl font-mono font-bold text-green-700">
                            {formatCurrency(isCreate ? 0 : cashReceived)}
                          </p>
                        </div>
                        <div className={`text-center p-4 rounded-lg ${
                          differenceStatus === 'match' ? 'bg-green-50' :
                          differenceStatus === 'short' ? 'bg-red-50' : 'bg-yellow-50'
                        }`}>
                          <p className="text-sm text-gray-500 mb-1">Selisih</p>
                          <p className={`text-xl font-mono font-bold ${
                            differenceStatus === 'match' ? 'text-green-700' :
                            differenceStatus === 'short' ? 'text-red-700' : 'text-yellow-700'
                          }`}>
                            {formatCurrency(isCreate ? 0 : difference)}
                          </p>
                        </div>
                      </div>

                      {!isCreate && depositData?.difference_reason && (
                        <div className="p-4 bg-gray-50 rounded-lg">
                          <p className="text-sm font-medium text-gray-700 mb-2">Alasan Selisih:</p>
                          <p className="text-gray-600">{depositData.difference_reason}</p>
                        </div>
                      )}

                      {isCreate && (
                        <div className="p-4 bg-blue-50 rounded-lg text-center">
                          <p className="text-blue-700">
                            Selisih akan dihitung setelah setoran dibuat dan diinput nominal fisiknya
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Journal Tab */}
              {activeTab === 'journal' && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <BookOpen className="w-5 h-5" />
                      Jurnal Akuntansi
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {depositData?.journal_number ? (
                      <div className="space-y-4">
                        <div className="p-4 bg-purple-50 rounded-lg">
                          <p className="text-sm text-gray-500">Nomor Jurnal</p>
                          <p className="text-lg font-mono font-bold text-purple-700">
                            {depositData.journal_number}
                          </p>
                          <p className="text-sm text-gray-500 mt-2">
                            Posted: {formatDate(depositData.posted_at)}
                          </p>
                        </div>
                        
                        <div className="bg-gray-50 rounded-lg p-4">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b">
                                <th className="text-left py-2">Akun</th>
                                <th className="text-right py-2">Debit</th>
                                <th className="text-right py-2">Kredit</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr className="border-b">
                                <td className="py-2">1101 - Kas Kecil Pusat</td>
                                <td className="py-2 text-right font-mono">{formatCurrency(depositData.cash_received)}</td>
                                <td className="py-2 text-right">-</td>
                              </tr>
                              {depositData.difference_amount < 0 && (
                                <tr className="border-b text-red-600">
                                  <td className="py-2">6201 - Selisih Kurang Kas</td>
                                  <td className="py-2 text-right font-mono">{formatCurrency(Math.abs(depositData.difference_amount))}</td>
                                  <td className="py-2 text-right">-</td>
                                </tr>
                              )}
                              {depositData.difference_amount > 0 && (
                                <tr className="border-b text-yellow-600">
                                  <td className="py-2">4201 - Selisih Lebih Kas</td>
                                  <td className="py-2 text-right">-</td>
                                  <td className="py-2 text-right font-mono">{formatCurrency(Math.abs(depositData.difference_amount))}</td>
                                </tr>
                              )}
                              <tr>
                                <td className="py-2">1102 - Kas Cabang</td>
                                <td className="py-2 text-right">-</td>
                                <td className="py-2 text-right font-mono">{formatCurrency(depositData.cash_should_deposit)}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <BookOpen className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                        <p>Jurnal akan dibuat setelah setoran di-posting</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t bg-gray-50 flex justify-between items-center">
          <div className="text-sm text-gray-500">
            {!isCreate && depositData && (
              <>
                Dibuat oleh: {depositData.created_by_name} | {formatDate(depositData.created_at)}
              </>
            )}
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onClose(false)}>
              Tutup
            </Button>
            
            {/* Create button */}
            {isCreate && salesData?.summary?.total_transactions > 0 && (
              <Button onClick={handleCreate} disabled={saving} className="bg-blue-600 hover:bg-blue-700">
                {saving ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                Buat Setoran
              </Button>
            )}
            
            {/* Update button */}
            {isEdit && canEdit && (
              <Button onClick={handleUpdate} disabled={saving} className="bg-blue-600 hover:bg-blue-700">
                {saving ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                Simpan
              </Button>
            )}

            {/* Action buttons based on status */}
            {!isCreate && depositData && (
              <>
                {depositData.status === 'pending' && (
                  <Button onClick={() => handleAction('receive')} disabled={saving} className="bg-green-600 hover:bg-green-700">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Terima Setoran
                  </Button>
                )}
                
                {depositData.status === 'received' && (
                  <Button onClick={() => handleAction('verify')} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Verifikasi
                  </Button>
                )}
                
                {depositData.status === 'verified' && (
                  <Button onClick={() => handleAction('approve')} disabled={saving} className="bg-teal-600 hover:bg-teal-700">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Approve
                  </Button>
                )}
                
                {depositData.status === 'approved' && (
                  <Button onClick={() => handleAction('post')} disabled={saving} className="bg-purple-600 hover:bg-purple-700">
                    <FileText className="w-4 h-4 mr-2" />
                    Posting ke Jurnal
                  </Button>
                )}
                
                {['draft', 'pending'].includes(depositData.status) && (
                  <Button onClick={() => handleAction('cancel')} disabled={saving} variant="destructive">
                    <Ban className="w-4 h-4 mr-2" />
                    Batalkan
                  </Button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
