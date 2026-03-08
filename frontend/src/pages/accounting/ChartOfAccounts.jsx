import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Edit2, Trash2, Loader2, X, FileText, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';

const ChartOfAccounts = () => {
  const { api } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    code: '', name: '', category: 'asset', parent_id: '', 
    account_type: 'detail', is_cash: false, is_active: true, 
    description: '', normal_balance: 'debit'
  });

  const categories = [
    { value: 'asset', label: 'Aset', color: 'bg-blue-600/20 text-blue-400' },
    { value: 'liability', label: 'Kewajiban', color: 'bg-red-600/20 text-red-400' },
    { value: 'equity', label: 'Modal', color: 'bg-purple-600/20 text-purple-400' },
    { value: 'revenue', label: 'Pendapatan', color: 'bg-green-600/20 text-green-400' },
    { value: 'expense', label: 'Beban', color: 'bg-yellow-600/20 text-yellow-400' }
  ];

  const loadAccounts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(categoryFilter && { category: categoryFilter }),
        include_inactive: 'true'
      });
      const res = await api(`/api/accounting/accounts?${params}`);
      if (res.ok) {
        const data = await res.json();
        setAccounts(data.items || []);
      }
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, searchTerm, categoryFilter]);

  useEffect(() => { loadAccounts(); }, [loadAccounts]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingItem 
        ? `/api/accounting/accounts/${editingItem.id}` 
        : '/api/accounting/accounts';
      const res = await api(url, { 
        method: editingItem ? 'PUT' : 'POST', 
        body: JSON.stringify(formData) 
      });
      if (res.ok) {
        toast.success(editingItem ? 'Akun berhasil diupdate' : 'Akun berhasil ditambahkan');
        setShowModal(false);
        resetForm();
        loadAccounts();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menyimpan');
      }
    } catch (err) { toast.error('Gagal menyimpan'); }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setFormData({
      code: item.code || '',
      name: item.name || '',
      category: item.category || 'asset',
      parent_id: item.parent_id || '',
      account_type: item.account_type || 'detail',
      is_cash: item.is_cash || false,
      is_active: item.is_active !== false,
      description: item.description || '',
      normal_balance: item.normal_balance || 'debit'
    });
    setShowModal(true);
  };

  const handleDelete = async (item) => {
    if (!confirm(`Hapus akun "${item.name}"?`)) return;
    try {
      const res = await api(`/api/accounting/accounts/${item.id}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Akun berhasil dihapus');
        loadAccounts();
      }
    } catch { toast.error('Gagal menghapus'); }
  };

  const resetForm = () => {
    setEditingItem(null);
    setFormData({
      code: '', name: '', category: 'asset', parent_id: '',
      account_type: 'detail', is_cash: false, is_active: true,
      description: '', normal_balance: 'debit'
    });
  };

  const getCategoryBadge = (category) => {
    const cat = categories.find(c => c.value === category);
    return cat ? <span className={`px-2 py-1 rounded text-xs ${cat.color}`}>{cat.label}</span> : category;
  };

  return (
    <div className="space-y-4" data-testid="chart-of-accounts-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Daftar Perkiraan</h1>
          <p className="text-gray-400 text-sm">Chart of Accounts - Kelola akun perkiraan</p>
        </div>
        <button onClick={() => { resetForm(); setShowModal(true); }}
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-4 w-4" /> Tambah Akun
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-5 gap-4">
        {categories.map(cat => (
          <div key={cat.value} className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
            <p className="text-gray-400 text-sm">{cat.label}</p>
            <p className="text-2xl font-bold text-amber-200">
              {accounts.filter(a => a.category === cat.value).length}
            </p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input type="text" placeholder="Cari kode/nama akun..." value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
          </div>
          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200">
            <option value="">Semua Kategori</option>
            {categories.map(cat => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA AKUN</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">KATEGORI</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">TIPE</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">SALDO NORMAL</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">SALDO</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : accounts.length === 0 ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Belum ada data akun</td></tr>
              ) : accounts.map(account => (
                <tr key={account.id} className={`hover:bg-red-900/10 ${!account.is_active ? 'opacity-50' : ''}`}>
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{account.code}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-gray-500" />
                      <span className="font-medium text-gray-200">{account.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">{getCategoryBadge(account.category)}</td>
                  <td className="px-4 py-3 text-center text-sm text-gray-400">
                    {account.account_type === 'header' ? 'Header' : 'Detail'}
                  </td>
                  <td className="px-4 py-3 text-center text-sm text-gray-400">
                    {account.normal_balance === 'debit' ? 'Debit' : 'Kredit'}
                  </td>
                  <td className="px-4 py-3 text-right text-sm font-medium text-green-400">
                    Rp {(account.balance || 0).toLocaleString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      account.is_active ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'
                    }`}>
                      {account.is_active ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button onClick={() => handleEdit(account)} className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400">
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button onClick={() => handleDelete(account)} className="p-1.5 hover:bg-red-600/20 rounded text-red-400">
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

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">{editingItem ? 'Edit' : 'Tambah'} Akun Perkiraan</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kode Akun *</label>
                  <input type="text" value={formData.code} onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required placeholder="1-1001" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nama Akun *</label>
                  <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required placeholder="Kas" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kategori *</label>
                  <select value={formData.category} onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    {categories.map(cat => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tipe Akun</label>
                  <select value={formData.account_type} onChange={(e) => setFormData({ ...formData, account_type: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="header">Header (Induk)</option>
                    <option value="detail">Detail</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Saldo Normal</label>
                  <select value={formData.normal_balance} onChange={(e) => setFormData({ ...formData, normal_balance: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="debit">Debit</option>
                    <option value="credit">Kredit</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Akun Induk</label>
                  <select value={formData.parent_id} onChange={(e) => setFormData({ ...formData, parent_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="">Tidak Ada</option>
                    {accounts.filter(a => a.account_type === 'header').map(a => (
                      <option key={a.id} value={a.id}>{a.code} - {a.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Deskripsi</label>
                <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
              </div>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={formData.is_cash} onChange={(e) => setFormData({ ...formData, is_cash: e.target.checked })} />
                  <span className="text-sm text-gray-300">Akun Kas</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={formData.is_active} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} />
                  <span className="text-sm text-gray-300">Aktif</span>
                </label>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button>
                <button type="submit" className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">
                  {editingItem ? 'Update' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChartOfAccounts;
