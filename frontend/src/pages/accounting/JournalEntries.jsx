import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Edit2, Trash2, Loader2, X, FileText, Download, Printer, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const JournalEntries = () => {
  const { api } = useAuth();
  const [journals, setJournals] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showUnbalanced, setShowUnbalanced] = useState(false);
  const [unbalancedJournals, setUnbalancedJournals] = useState([]);
  const [editingItem, setEditingItem] = useState(null);
  const [totals, setTotals] = useState({ debit: 0, credit: 0 });
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    reference: '',
    description: '',
    entries: [
      { account_id: '', debit: 0, credit: 0, description: '' },
      { account_id: '', debit: 0, credit: 0, description: '' }
    ]
  });

  const loadJournals = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(dateFrom && { date_from: dateFrom }),
        ...(dateTo && { date_to: dateTo })
      });
      const res = await api(`/api/accounting/journals?${params}`);
      if (res.ok) {
        const data = await res.json();
        setJournals(data.items || []);
        setTotals({ debit: data.total_debit || 0, credit: data.total_credit || 0 });
      }
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, searchTerm, dateFrom, dateTo]);

  const loadAccounts = useCallback(async () => {
    try {
      const res = await api('/api/accounting/accounts?include_inactive=false');
      if (res.ok) {
        const data = await res.json();
        setAccounts(data.items || []);
      }
    } catch (err) { console.error('Error loading accounts'); }
  }, [api]);

  const loadUnbalanced = useCallback(async () => {
    try {
      const res = await api('/api/accounting/journals/unbalanced');
      if (res.ok) {
        const data = await res.json();
        setUnbalancedJournals(data.items || []);
      }
    } catch (err) { console.error('Error loading unbalanced'); }
  }, [api]);

  useEffect(() => { 
    loadJournals(); 
    loadAccounts();
    loadUnbalanced();
  }, [loadJournals, loadAccounts, loadUnbalanced]);

  const addEntry = () => {
    setFormData({
      ...formData,
      entries: [...formData.entries, { account_id: '', debit: 0, credit: 0, description: '' }]
    });
  };

  const removeEntry = (index) => {
    if (formData.entries.length <= 2) {
      toast.error('Minimal 2 baris jurnal');
      return;
    }
    const newEntries = formData.entries.filter((_, i) => i !== index);
    setFormData({ ...formData, entries: newEntries });
  };

  const updateEntry = (index, field, value) => {
    const newEntries = [...formData.entries];
    newEntries[index][field] = value;
    setFormData({ ...formData, entries: newEntries });
  };

  const calculateTotals = () => {
    const totalDebit = formData.entries.reduce((sum, e) => sum + (parseFloat(e.debit) || 0), 0);
    const totalCredit = formData.entries.reduce((sum, e) => sum + (parseFloat(e.credit) || 0), 0);
    return { totalDebit, totalCredit, isBalanced: Math.abs(totalDebit - totalCredit) < 0.01 };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { isBalanced } = calculateTotals();
    if (!isBalanced) {
      toast.error('Jurnal tidak seimbang. Debit harus sama dengan Kredit.');
      return;
    }
    
    try {
      const url = editingItem ? `/api/accounting/journals/${editingItem.id}` : '/api/accounting/journals';
      const res = await api(url, {
        method: editingItem ? 'PUT' : 'POST',
        body: JSON.stringify({
          ...formData,
          entries: formData.entries.filter(e => e.account_id && (e.debit > 0 || e.credit > 0)),
          source: 'manual'
        })
      });
      if (res.ok) {
        toast.success(editingItem ? 'Jurnal berhasil diupdate' : 'Jurnal berhasil dibuat');
        setShowModal(false);
        resetForm();
        loadJournals();
        loadUnbalanced();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menyimpan');
      }
    } catch (err) { toast.error('Gagal menyimpan'); }
  };

  const handleEdit = (journal) => {
    setEditingItem(journal);
    setFormData({
      date: journal.date || '',
      reference: journal.reference || '',
      description: journal.description || '',
      entries: journal.entries?.length > 0 ? journal.entries : [
        { account_id: '', debit: 0, credit: 0, description: '' },
        { account_id: '', debit: 0, credit: 0, description: '' }
      ]
    });
    setShowModal(true);
  };

  const handleDelete = async (journal) => {
    if (!confirm(`Hapus jurnal "${journal.journal_number}"?`)) return;
    try {
      const res = await api(`/api/accounting/journals/${journal.id}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Jurnal berhasil dihapus');
        loadJournals();
        loadUnbalanced();
      }
    } catch { toast.error('Gagal menghapus'); }
  };

  const resetForm = () => {
    setEditingItem(null);
    setFormData({
      date: new Date().toISOString().split('T')[0],
      reference: '',
      description: '',
      entries: [
        { account_id: '', debit: 0, credit: 0, description: '' },
        { account_id: '', debit: 0, credit: 0, description: '' }
      ]
    });
  };

  const { totalDebit, totalCredit, isBalanced } = calculateTotals();

  return (
    <div className="space-y-4" data-testid="journal-entries-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Data Jurnal</h1>
          <p className="text-gray-400 text-sm">Kelola jurnal umum</p>
        </div>
        <div className="flex gap-2">
          {unbalancedJournals.length > 0 && (
            <button onClick={() => setShowUnbalanced(true)}
              className="px-4 py-2 bg-red-600/20 text-red-400 rounded-lg flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" /> {unbalancedJournals.length} Tidak Seimbang
            </button>
          )}
          <button onClick={() => { resetForm(); setShowModal(true); }}
            className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
            <Plus className="h-4 w-4" /> Tambah Jurnal
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total Jurnal</p>
          <p className="text-2xl font-bold text-amber-200">{journals.length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total Debit</p>
          <p className="text-2xl font-bold text-blue-400">Rp {totals.debit.toLocaleString('id-ID')}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total Kredit</p>
          <p className="text-2xl font-bold text-green-400">Rp {totals.credit.toLocaleString('id-ID')}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input type="text" placeholder="Cari jurnal..." value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
          </div>
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
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. JURNAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KETERANGAN</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">DEBIT</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">KREDIT</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">SUMBER</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : journals.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Belum ada data jurnal</td></tr>
              ) : journals.map(journal => (
                <tr key={journal.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{journal.journal_number}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {new Date(journal.date).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-200">{journal.description}</td>
                  <td className="px-4 py-3 text-sm text-right text-blue-400">
                    Rp {(journal.total_debit || 0).toLocaleString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-green-400">
                    Rp {(journal.total_credit || 0).toLocaleString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded text-xs ${
                      journal.source === 'manual' ? 'bg-gray-600/20 text-gray-400' : 'bg-blue-600/20 text-blue-400'
                    }`}>
                      {journal.source === 'manual' ? 'Manual' : journal.source}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button onClick={() => handleEdit(journal)} className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400">
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button onClick={() => handleDelete(journal)} className="p-1.5 hover:bg-red-600/20 rounded text-red-400">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">{editingItem ? 'Edit' : 'Tambah'} Jurnal</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tanggal *</label>
                  <input type="date" value={formData.date} onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Referensi</label>
                  <input type="text" value={formData.reference} onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" placeholder="No. Bukti" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Keterangan *</label>
                  <input type="text" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required placeholder="Keterangan jurnal" />
                </div>
              </div>

              <div className="border border-red-900/30 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs text-amber-200">AKUN</th>
                      <th className="px-3 py-2 text-left text-xs text-amber-200">KETERANGAN</th>
                      <th className="px-3 py-2 text-right text-xs text-amber-200">DEBIT</th>
                      <th className="px-3 py-2 text-right text-xs text-amber-200">KREDIT</th>
                      <th className="px-3 py-2 w-10"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-900/20">
                    {formData.entries.map((entry, idx) => (
                      <tr key={idx}>
                        <td className="px-3 py-2">
                          <select value={entry.account_id} onChange={(e) => updateEntry(idx, 'account_id', e.target.value)}
                            className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm">
                            <option value="">Pilih Akun</option>
                            {accounts.map(a => (
                              <option key={a.id} value={a.id}>{a.code} - {a.name}</option>
                            ))}
                          </select>
                        </td>
                        <td className="px-3 py-2">
                          <input type="text" value={entry.description} onChange={(e) => updateEntry(idx, 'description', e.target.value)}
                            className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm" />
                        </td>
                        <td className="px-3 py-2">
                          <input type="number" min="0" value={entry.debit} onChange={(e) => updateEntry(idx, 'debit', parseFloat(e.target.value) || 0)}
                            className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm text-right" />
                        </td>
                        <td className="px-3 py-2">
                          <input type="number" min="0" value={entry.credit} onChange={(e) => updateEntry(idx, 'credit', parseFloat(e.target.value) || 0)}
                            className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm text-right" />
                        </td>
                        <td className="px-3 py-2">
                          <button type="button" onClick={() => removeEntry(idx)} className="p-1 hover:bg-red-600/20 rounded text-red-400">
                            <X className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-red-900/10">
                      <td colSpan={2} className="px-3 py-2 text-right font-semibold text-amber-200">TOTAL:</td>
                      <td className="px-3 py-2 text-right font-bold text-blue-400">Rp {totalDebit.toLocaleString('id-ID')}</td>
                      <td className="px-3 py-2 text-right font-bold text-green-400">Rp {totalCredit.toLocaleString('id-ID')}</td>
                      <td></td>
                    </tr>
                  </tbody>
                </table>
                <div className="p-2 border-t border-red-900/30 flex justify-between items-center">
                  <button type="button" onClick={addEntry} className="px-3 py-1 bg-blue-600/20 text-blue-400 rounded text-sm flex items-center gap-1">
                    <Plus className="h-3 w-3" /> Tambah Baris
                  </button>
                  <span className={`px-3 py-1 rounded text-sm ${isBalanced ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'}`}>
                    {isBalanced ? 'SEIMBANG' : `SELISIH: Rp ${Math.abs(totalDebit - totalCredit).toLocaleString('id-ID')}`}
                  </span>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button>
                <button type="submit" disabled={!isBalanced} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50">
                  {editingItem ? 'Update' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Unbalanced Modal */}
      {showUnbalanced && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-red-400 flex items-center gap-2">
                <AlertTriangle /> Jurnal Tidak Seimbang
              </h2>
              <button onClick={() => setShowUnbalanced(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-4">
              <table className="w-full">
                <thead className="bg-red-900/20">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs text-amber-200">NO. JURNAL</th>
                    <th className="px-3 py-2 text-left text-xs text-amber-200">TANGGAL</th>
                    <th className="px-3 py-2 text-right text-xs text-amber-200">DEBIT</th>
                    <th className="px-3 py-2 text-right text-xs text-amber-200">KREDIT</th>
                    <th className="px-3 py-2 text-right text-xs text-amber-200">SELISIH</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-red-900/20">
                  {unbalancedJournals.map(j => (
                    <tr key={j.id} className="hover:bg-red-900/10">
                      <td className="px-3 py-2 text-sm font-mono text-amber-300">{j.journal_number}</td>
                      <td className="px-3 py-2 text-sm text-gray-400">{new Date(j.date).toLocaleDateString('id-ID')}</td>
                      <td className="px-3 py-2 text-sm text-right text-blue-400">Rp {(j.total_debit || 0).toLocaleString('id-ID')}</td>
                      <td className="px-3 py-2 text-sm text-right text-green-400">Rp {(j.total_credit || 0).toLocaleString('id-ID')}</td>
                      <td className="px-3 py-2 text-sm text-right text-red-400">Rp {Math.abs(j.difference || 0).toLocaleString('id-ID')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JournalEntries;
