import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Eye, Check, Loader2, Calendar, Wallet, X } from 'lucide-react';
import { toast } from 'sonner';

const PurchasePayments = () => {
  const { api } = useAuth();
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [purchases, setPurchases] = useState([]);
  const [banks, setBanks] = useState([]);
  const [formData, setFormData] = useState({
    po_id: '', amount: 0, payment_method: 'transfer', bank_id: '', reference: '', notes: ''
  });

  const loadPayments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/purchase/payments?search=${searchTerm}`);
      if (res.ok) {
        const data = await res.json();
        setPayments(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm]);

  const loadMasterData = useCallback(async () => {
    try {
      const [poRes, bankRes] = await Promise.all([
        api('/api/purchase/orders?status=submitted,partial'),
        api('/api/master/banks')
      ]);
      if (poRes.ok) {
        const data = await poRes.json();
        setPurchases(data.items || data || []);
      }
      if (bankRes.ok) setBanks(await bankRes.json());
    } catch (err) {
      console.error('Error loading master data');
    }
  }, [api]);

  useEffect(() => {
    loadPayments();
    loadMasterData();
  }, [loadPayments, loadMasterData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await api('/api/purchase/payments', {
        method: 'POST',
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        toast.success('Pembayaran berhasil dicatat');
        setShowModal(false);
        resetForm();
        loadPayments();
      }
    } catch (err) {
      toast.error('Gagal menyimpan pembayaran');
    }
  };

  const resetForm = () => {
    setFormData({ po_id: '', amount: 0, payment_method: 'transfer', bank_id: '', reference: '', notes: '' });
  };

  return (
    <div className="space-y-4" data-testid="purchase-payments-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Daftar Pembayaran</h1>
          <p className="text-gray-400 text-sm">Kelola pembayaran ke supplier</p>
        </div>
        <button onClick={() => { resetForm(); setShowModal(true); }}
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-4 w-4" /> Catat Pembayaran
        </button>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Cari pembayaran..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. PEMBAYARAN</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. PO</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">SUPPLIER</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">JUMLAH</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">METODE</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : payments.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Belum ada data pembayaran</td></tr>
              ) : payments.map(payment => (
                <tr key={payment.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{payment.payment_number || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {new Date(payment.created_at).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300">{payment.po_number}</td>
                  <td className="px-4 py-3 text-sm text-gray-200">{payment.supplier_name}</td>
                  <td className="px-4 py-3 text-sm text-right text-green-400 font-medium">
                    Rp {(payment.amount || 0).toLocaleString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-1 bg-blue-600/20 text-blue-400 rounded text-xs">
                      {payment.payment_method === 'transfer' ? 'Transfer' : 
                       payment.payment_method === 'cash' ? 'Tunai' : 
                       payment.payment_method === 'check' ? 'Cek/Giro' : payment.payment_method}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-1 bg-green-600/20 text-green-400 rounded-full text-xs">
                      Lunas
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Payment Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">Catat Pembayaran</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Purchase Order *</label>
                <select value={formData.po_id} onChange={(e) => setFormData({ ...formData, po_id: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                  <option value="">Pilih PO</option>
                  {purchases.map(po => (
                    <option key={po.id} value={po.id}>{po.po_number} - {po.supplier_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah Pembayaran (Rp) *</label>
                <input type="number" min="0" value={formData.amount} 
                  onChange={(e) => setFormData({ ...formData, amount: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Metode Pembayaran</label>
                  <select value={formData.payment_method} onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="transfer">Transfer Bank</option>
                    <option value="cash">Tunai</option>
                    <option value="check">Cek/Giro</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Bank</label>
                  <select value={formData.bank_id} onChange={(e) => setFormData({ ...formData, bank_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="">Pilih Bank</option>
                    {banks.map(bank => (
                      <option key={bank.id} value={bank.id}>{bank.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Referensi/No. Bukti</label>
                <input type="text" value={formData.reference} 
                  onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                  placeholder="No. transfer, no. cek, dll"
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
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

export default PurchasePayments;
