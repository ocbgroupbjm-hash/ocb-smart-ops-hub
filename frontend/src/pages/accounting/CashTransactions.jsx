import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Loader2, X, ArrowDownLeft, ArrowUpRight, ArrowLeftRight, Wallet } from 'lucide-react';
import { toast } from 'sonner';

const CashTransactions = () => {
  const { api } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [totals, setTotals] = useState({ in: 0, out: 0 });
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    transaction_type: 'cash_in',
    account_id: '',
    to_account_id: '',
    amount: 0,
    description: '',
    reference: ''
  });

  const loadTransactions = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(typeFilter && { transaction_type: typeFilter }),
        ...(dateFrom && { date_from: dateFrom }),
        ...(dateTo && { date_to: dateTo })
      });
      const res = await api(`/api/accounting/cash?${params}`);
      if (res.ok) {
        const data = await res.json();
        setTransactions(data.items || []);
        setTotals({ in: data.total_in || 0, out: data.total_out || 0 });
      }
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, typeFilter, dateFrom, dateTo]);

  const loadAccounts = useCallback(async () => {
    try {
      const res = await api('/api/accounting/accounts?include_inactive=false');
      if (res.ok) {
        const data = await res.json();
        setAccounts(data.items?.filter(a => a.is_cash || a.category === 'asset') || []);
      }
    } catch (err) { console.error('Error loading accounts'); }
  }, [api]);

  useEffect(() => { 
    loadTransactions(); 
    loadAccounts();
  }, [loadTransactions, loadAccounts]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await api('/api/accounting/cash', {
        method: 'POST',
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        toast.success('Transaksi kas berhasil dicatat');
        setShowModal(false);
        resetForm();
        loadTransactions();
      }
    } catch (err) { toast.error('Gagal menyimpan'); }
  };

  const resetForm = () => {
    setFormData({
      date: new Date().toISOString().split('T')[0],
      transaction_type: 'cash_in',
      account_id: '',
      to_account_id: '',
      amount: 0,
      description: '',
      reference: ''
    });
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'cash_in': return <ArrowDownLeft className="h-4 w-4 text-green-400" />;
      case 'cash_out': return <ArrowUpRight className="h-4 w-4 text-red-400" />;
      case 'transfer': return <ArrowLeftRight className="h-4 w-4 text-blue-400" />;
      default: return <Wallet className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case 'cash_in': return 'Kas Masuk';
      case 'cash_out': return 'Kas Keluar';
      case 'transfer': return 'Transfer';
      default: return type;
    }
  };

  return (
    <div className="space-y-4" data-testid="cash-transactions-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Kas Masuk/Keluar/Transfer</h1>
          <p className="text-gray-400 text-sm">Kelola transaksi kas perusahaan</p>
        </div>
        <button onClick={() => { resetForm(); setShowModal(true); }}
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-4 w-4" /> Tambah Transaksi
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Kas Masuk</p>
          <p className="text-2xl font-bold text-green-400">Rp {totals.in.toLocaleString('id-ID')}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Kas Keluar</p>
          <p className="text-2xl font-bold text-red-400">Rp {totals.out.toLocaleString('id-ID')}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Saldo Bersih</p>
          <p className={`text-2xl font-bold ${totals.in - totals.out >= 0 ? 'text-amber-200' : 'text-red-400'}`}>
            Rp {(totals.in - totals.out).toLocaleString('id-ID')}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200">
            <option value="">Semua Tipe</option>
            <option value="cash_in">Kas Masuk</option>
            <option value="cash_out">Kas Keluar</option>
            <option value="transfer">Transfer</option>
          </select>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. TRANSAKSI</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">TIPE</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">AKUN</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KETERANGAN</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">JUMLAH</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : transactions.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Belum ada transaksi kas</td></tr>
              ) : transactions.map(trans => (
                <tr key={trans.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{trans.transaction_number}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {new Date(trans.date).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="flex items-center justify-center gap-1">
                      {getTypeIcon(trans.transaction_type)}
                      <span className="text-sm text-gray-300">{getTypeLabel(trans.transaction_type)}</span>
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-200">
                    {trans.account_name}
                    {trans.to_account_name && <span className="text-gray-500"> → {trans.to_account_name}</span>}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">{trans.description}</td>
                  <td className={`px-4 py-3 text-sm text-right font-medium ${
                    trans.transaction_type === 'cash_in' ? 'text-green-400' : 
                    trans.transaction_type === 'cash_out' ? 'text-red-400' : 'text-blue-400'
                  }`}>
                    Rp {(trans.amount || 0).toLocaleString('id-ID')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">Transaksi Kas</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tanggal *</label>
                  <input type="date" value={formData.date} onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tipe Transaksi *</label>
                  <select value={formData.transaction_type} onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="cash_in">Kas Masuk</option>
                    <option value="cash_out">Kas Keluar</option>
                    <option value="transfer">Transfer</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  {formData.transaction_type === 'transfer' ? 'Dari Akun' : 'Akun Kas'} *
                </label>
                <select value={formData.account_id} onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                  <option value="">Pilih Akun</option>
                  {accounts.map(a => (
                    <option key={a.id} value={a.id}>{a.code} - {a.name}</option>
                  ))}
                </select>
              </div>
              {formData.transaction_type === 'transfer' && (
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Ke Akun *</label>
                  <select value={formData.to_account_id} onChange={(e) => setFormData({ ...formData, to_account_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                    <option value="">Pilih Akun Tujuan</option>
                    {accounts.filter(a => a.id !== formData.account_id).map(a => (
                      <option key={a.id} value={a.id}>{a.code} - {a.name}</option>
                    ))}
                  </select>
                </div>
              )}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah (Rp) *</label>
                <input type="number" min="0" value={formData.amount} 
                  onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Keterangan *</label>
                <input type="text" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Referensi</label>
                <input type="text" value={formData.reference} onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" placeholder="No. Bukti" />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button>
                <button type="submit" className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">Simpan</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CashTransactions;
