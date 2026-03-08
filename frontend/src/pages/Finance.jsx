import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { DollarSign, TrendingUp, TrendingDown, Loader2, Plus, X, Calendar, RefreshCw, Wallet, ReceiptText, PiggyBank } from 'lucide-react';
import { toast } from 'sonner';

const Finance = () => {
  const { api, user } = useAuth();
  const [activeTab, setActiveTab] = useState('summary');
  const [loading, setLoading] = useState(true);
  const [balance, setBalance] = useState(null);
  const [movements, setMovements] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [dailyReport, setDailyReport] = useState(null);
  const [showCashInModal, setShowCashInModal] = useState(false);
  const [showCashOutModal, setShowCashOutModal] = useState(false);
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [cashForm, setCashForm] = useState({ amount: 0, category: 'other', description: '' });
  const [expenseForm, setExpenseForm] = useState({ category: '', description: '', amount: 0, payment_method: 'cash', date: new Date().toISOString().slice(0, 10) });
  const [saving, setSaving] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().slice(0, 10));

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  useEffect(() => {
    if (activeTab === 'summary') { loadBalance(); loadDailyReport(); }
    else if (activeTab === 'cash') loadCashMovements();
    else if (activeTab === 'expenses') loadExpenses();
  }, [activeTab, selectedDate]);

  const loadBalance = async () => {
    try {
      const res = await api('/api/finance/cash/balance');
      if (res.ok) setBalance(await res.json());
    } catch (err) { console.error(err); }
  };

  const loadDailyReport = async () => {
    setLoading(true);
    try {
      const res = await api(`/api/finance/reports/daily?date=${selectedDate}`);
      if (res.ok) setDailyReport(await res.json());
    } catch (err) { toast.error('Gagal memuat laporan'); }
    finally { setLoading(false); }
  };

  const loadCashMovements = async () => {
    setLoading(true);
    try {
      const res = await api(`/api/finance/cash/movements?limit=100&date_from=${selectedDate}&date_to=${selectedDate}`);
      if (res.ok) { const data = await res.json(); setMovements(data.items || []); }
    } catch (err) { toast.error('Gagal memuat kas'); }
    finally { setLoading(false); }
  };

  const loadExpenses = async () => {
    setLoading(true);
    try {
      const res = await api(`/api/finance/expenses?limit=100&date_from=${selectedDate}&date_to=${selectedDate}`);
      if (res.ok) { const data = await res.json(); setExpenses(data.items || []); }
    } catch (err) { toast.error('Gagal memuat pengeluaran'); }
    finally { setLoading(false); }
  };

  const handleCashIn = async () => {
    if (cashForm.amount <= 0) { toast.error('Jumlah harus lebih dari 0'); return; }
    setSaving(true);
    try {
      const res = await api('/api/finance/cash/in', { method: 'POST', body: JSON.stringify(cashForm) });
      if (res.ok) { toast.success('Kas masuk tercatat'); setShowCashInModal(false); setCashForm({ amount: 0, category: 'other', description: '' }); loadBalance(); loadCashMovements(); }
    } catch (err) { toast.error('Gagal mencatat kas'); }
    finally { setSaving(false); }
  };

  const handleCashOut = async () => {
    if (cashForm.amount <= 0) { toast.error('Jumlah harus lebih dari 0'); return; }
    setSaving(true);
    try {
      const res = await api('/api/finance/cash/out', { method: 'POST', body: JSON.stringify(cashForm) });
      if (res.ok) { toast.success('Kas keluar tercatat'); setShowCashOutModal(false); setCashForm({ amount: 0, category: 'other', description: '' }); loadBalance(); loadCashMovements(); }
      else { const error = await res.json(); toast.error(error.detail || 'Gagal'); }
    } catch (err) { toast.error('Gagal mencatat kas'); }
    finally { setSaving(false); }
  };

  const handleExpense = async () => {
    if (!expenseForm.category || expenseForm.amount <= 0) { toast.error('Kategori dan jumlah wajib diisi'); return; }
    setSaving(true);
    try {
      const res = await api('/api/finance/expenses', { method: 'POST', body: JSON.stringify(expenseForm) });
      if (res.ok) { toast.success('Pengeluaran tercatat'); setShowExpenseModal(false); setExpenseForm({ category: '', description: '', amount: 0, payment_method: 'cash', date: selectedDate }); loadExpenses(); loadBalance(); }
    } catch (err) { toast.error('Gagal mencatat pengeluaran'); }
    finally { setSaving(false); }
  };

  const tabs = [
    { id: 'summary', label: 'Ringkasan', icon: DollarSign },
    { id: 'cash', label: 'Kas', icon: Wallet },
    { id: 'expenses', label: 'Pengeluaran', icon: ReceiptText }
  ];

  const expenseCategories = [
    'Gaji', 'Listrik', 'Air', 'Internet', 'Sewa', 'Transportasi', 'Perlengkapan', 'Maintenance', 'Marketing', 'Lainnya'
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Keuangan</h1>
          <p className="text-gray-400">{user?.branch?.name || 'Semua Cabang'}</p>
        </div>
        <div className="flex gap-2">
          <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} className="px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg" />
          <button onClick={() => setShowCashInModal(true)} className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg flex items-center gap-2">
            <TrendingUp className="h-4 w-4" /> Kas Masuk
          </button>
          <button onClick={() => setShowCashOutModal(true)} className="px-4 py-2 bg-red-600/20 text-red-400 rounded-lg flex items-center gap-2">
            <TrendingDown className="h-4 w-4" /> Kas Keluar
          </button>
        </div>
      </div>

      {/* Saldo Kas */}
      {balance && (
        <div className="bg-gradient-to-br from-amber-600/20 to-amber-900/10 border border-amber-800/30 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <PiggyBank className="h-8 w-8 text-amber-400" />
            <div>
              <div className="text-gray-400">Saldo Kas Saat Ini</div>
              <div className="text-3xl font-bold text-amber-400">{formatRupiah(balance.cash_balance)}</div>
            </div>
          </div>
          <div className="text-sm text-gray-400">{balance.branch_name}</div>
        </div>
      )}

      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${activeTab === tab.id ? 'bg-red-900/30 text-amber-400' : 'text-gray-400 hover:text-white hover:bg-red-900/20'}`}>
            <tab.icon className="h-4 w-4" /> {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Ringkasan */}
      {activeTab === 'summary' && (
        loading ? (
          <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-red-400" /></div>
        ) : dailyReport ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
              <div className="text-gray-400 mb-1">Penjualan</div>
              <div className="text-2xl font-bold text-green-400">{formatRupiah(dailyReport.sales?.total)}</div>
              <div className="text-sm text-gray-500">{dailyReport.sales?.transactions || 0} transaksi</div>
            </div>
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
              <div className="text-gray-400 mb-1">HPP</div>
              <div className="text-2xl font-bold text-gray-300">{formatRupiah(dailyReport.sales?.cost)}</div>
            </div>
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
              <div className="text-gray-400 mb-1">Laba Kotor</div>
              <div className="text-2xl font-bold text-amber-400">{formatRupiah(dailyReport.sales?.profit)}</div>
            </div>
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5">
              <div className="text-gray-400 mb-1">Pengeluaran</div>
              <div className="text-2xl font-bold text-red-400">{formatRupiah(dailyReport.expenses?.total)}</div>
            </div>
            <div className="bg-gradient-to-br from-green-600/20 to-green-900/10 border border-green-800/30 rounded-xl p-5 md:col-span-2">
              <div className="text-gray-400 mb-1">Laba Bersih</div>
              <div className="text-3xl font-bold text-green-400">{formatRupiah(dailyReport.net_profit)}</div>
            </div>
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5 md:col-span-2">
              <div className="text-gray-400 mb-1">Kas</div>
              <div className="flex justify-between">
                <div><div className="text-sm text-gray-500">Masuk</div><div className="text-lg font-bold text-green-400">{formatRupiah(dailyReport.cash?.in)}</div></div>
                <div><div className="text-sm text-gray-500">Keluar</div><div className="text-lg font-bold text-red-400">{formatRupiah(dailyReport.cash?.out)}</div></div>
                <div><div className="text-sm text-gray-500">Saldo</div><div className="text-lg font-bold text-amber-400">{formatRupiah(dailyReport.cash?.current_balance)}</div></div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">Tidak ada data untuk tanggal ini</div>
        )
      )}

      {/* Tab Kas */}
      {activeTab === 'cash' && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">Waktu</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Jenis</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Keterangan</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Jumlah</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Saldo</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
              ) : movements.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Tidak ada transaksi kas</td></tr>
              ) : (
                movements.map((mov, idx) => (
                  <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                    <td className="px-4 py-3 text-gray-400">{new Date(mov.created_at).toLocaleTimeString('id-ID')}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${mov.movement_type === 'cash_in' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                        {mov.movement_type === 'cash_in' ? 'Masuk' : 'Keluar'}
                      </span>
                    </td>
                    <td className="px-4 py-3">{mov.description}</td>
                    <td className={`px-4 py-3 text-right font-semibold ${mov.movement_type === 'cash_in' ? 'text-green-400' : 'text-red-400'}`}>
                      {mov.movement_type === 'cash_in' ? '+' : '-'}{formatRupiah(mov.amount)}
                    </td>
                    <td className="px-4 py-3 text-right text-amber-400">{formatRupiah(mov.balance_after)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab Pengeluaran */}
      {activeTab === 'expenses' && (
        <>
          <div className="flex justify-end">
            <button onClick={() => setShowExpenseModal(true)} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
              <Plus className="h-4 w-4" /> Catat Pengeluaran
            </button>
          </div>
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead className="bg-red-900/20">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Tanggal</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Kategori</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Keterangan</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Pembayaran</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Jumlah</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={5} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
                ) : expenses.length === 0 ? (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Tidak ada pengeluaran</td></tr>
                ) : (
                  expenses.map((exp, idx) => (
                    <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                      <td className="px-4 py-3 text-gray-400">{new Date(exp.date).toLocaleDateString('id-ID')}</td>
                      <td className="px-4 py-3 font-medium">{exp.category}</td>
                      <td className="px-4 py-3 text-gray-400">{exp.description}</td>
                      <td className="px-4 py-3 text-gray-400 capitalize">{exp.payment_method === 'cash' ? 'Tunai' : 'Transfer'}</td>
                      <td className="px-4 py-3 text-right text-red-400 font-semibold">{formatRupiah(exp.amount)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Modal Kas Masuk */}
      {showCashInModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2"><TrendingUp className="h-5 w-5 text-green-400" /> Kas Masuk</h2>
              <button onClick={() => setShowCashInModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah *</label>
                <input type="number" value={cashForm.amount} onChange={(e) => setCashForm({ ...cashForm, amount: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-xl" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Kategori</label>
                <select value={cashForm.category} onChange={(e) => setCashForm({ ...cashForm, category: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                  <option value="opening">Modal Awal</option>
                  <option value="deposit">Setor</option>
                  <option value="other">Lainnya</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Keterangan *</label>
                <input type="text" value={cashForm.description} onChange={(e) => setCashForm({ ...cashForm, description: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
              </div>
              <div className="flex gap-3">
                <button onClick={() => setShowCashInModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button onClick={handleCashIn} disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg disabled:opacity-50">
                  {saving ? 'Menyimpan...' : 'Simpan'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Kas Keluar */}
      {showCashOutModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2"><TrendingDown className="h-5 w-5 text-red-400" /> Kas Keluar</h2>
              <button onClick={() => setShowCashOutModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah *</label>
                <input type="number" value={cashForm.amount} onChange={(e) => setCashForm({ ...cashForm, amount: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-xl" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Kategori</label>
                <select value={cashForm.category} onChange={(e) => setCashForm({ ...cashForm, category: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                  <option value="withdrawal">Tarik</option>
                  <option value="closing">Tutup Kas</option>
                  <option value="other">Lainnya</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Keterangan *</label>
                <input type="text" value={cashForm.description} onChange={(e) => setCashForm({ ...cashForm, description: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
              </div>
              <div className="flex gap-3">
                <button onClick={() => setShowCashOutModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button onClick={handleCashOut} disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-rose-600 text-white rounded-lg disabled:opacity-50">
                  {saving ? 'Menyimpan...' : 'Simpan'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Pengeluaran */}
      {showExpenseModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Catat Pengeluaran</h2>
              <button onClick={() => setShowExpenseModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Kategori *</label>
                <select value={expenseForm.category} onChange={(e) => setExpenseForm({ ...expenseForm, category: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                  <option value="">Pilih Kategori</option>
                  {expenseCategories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Keterangan</label>
                <input type="text" value={expenseForm.description} onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah *</label>
                <input type="number" value={expenseForm.amount} onChange={(e) => setExpenseForm({ ...expenseForm, amount: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-xl" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Pembayaran</label>
                  <select value={expenseForm.payment_method} onChange={(e) => setExpenseForm({ ...expenseForm, payment_method: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="cash">Tunai</option>
                    <option value="bank_transfer">Transfer</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tanggal</label>
                  <input type="date" value={expenseForm.date} onChange={(e) => setExpenseForm({ ...expenseForm, date: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>
              <div className="flex gap-3">
                <button onClick={() => setShowExpenseModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button onClick={handleExpense} disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50">
                  {saving ? 'Menyimpan...' : 'Simpan'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Finance;
