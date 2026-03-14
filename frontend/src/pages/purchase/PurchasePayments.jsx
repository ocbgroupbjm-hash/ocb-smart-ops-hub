import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Loader2, X, Building2, Edit2, Trash2, RotateCcw, Eye, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { SearchableSelect } from '../../components/ui/searchable-select';
import { SearchableEnumSelect } from '../../components/ui/searchable-enum-select';
import { useSuppliers } from '../../hooks/useMasterData';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

// Payment method options
const paymentMethodOptions = [
  { value: 'transfer', label: 'Transfer Bank' },
  { value: 'cash', label: 'Tunai' },
  { value: 'check', label: 'Cek/Giro' },
];

// Status badge component
const StatusBadge = ({ status }) => {
  const statusConfig = {
    posted: { label: 'Posted', bg: 'bg-green-600/20', text: 'text-green-400' },
    draft: { label: 'Draft', bg: 'bg-yellow-600/20', text: 'text-yellow-400' },
    reversed: { label: 'Reversed', bg: 'bg-red-600/20', text: 'text-red-400' },
    deleted: { label: 'Deleted', bg: 'bg-gray-600/20', text: 'text-gray-400' },
  };
  const config = statusConfig[status] || statusConfig.posted;
  return (
    <span className={`px-2 py-1 ${config.bg} ${config.text} rounded-full text-xs`}>
      {config.label}
    </span>
  );
};

const PurchasePayments = () => {
  const { api, token } = useAuth();
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // create, edit, view
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showReversalConfirm, setShowReversalConfirm] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  
  // Use custom hook for suppliers
  const { data: supplierOptions, loading: suppliersLoading } = useSuppliers(token);
  const [payables, setPayables] = useState([]);
  const [loadingPayables, setLoadingPayables] = useState(false);
  const [banks, setBanks] = useState([]);
  const [loadingBanks, setLoadingBanks] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState('');
  
  const [formData, setFormData] = useState({
    ap_id: '',
    amount: 0,
    payment_method: 'transfer',
    bank_account_id: '',
    reference_no: '',
    notes: ''
  });

  const loadPayments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/ap/payments?search=${searchTerm}`);
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

  // FIX BUG 2: Correct API call for Cash/Bank accounts
  const loadBanks = useCallback(async () => {
    setLoadingBanks(true);
    try {
      // Use correct endpoint for cash/bank accounts
      const bankRes = await api('/api/accounts/cash-bank');
      if (bankRes.ok) {
        const data = await bankRes.json();
        const accs = data.accounts || data.items || [];
        if (accs.length > 0) {
          setBanks(accs.map(a => ({
            value: a.id || a.code,
            label: `${a.code} - ${a.name}`,
          })));
        } else {
          // Fallback: try accounting endpoint
          const fallbackRes = await api('/api/accounting/accounts/cash-bank');
          if (fallbackRes.ok) {
            const fallbackData = await fallbackRes.json();
            const fallbackAccs = fallbackData.accounts || fallbackData.items || [];
            setBanks(fallbackAccs.map(a => ({
              value: a.id || a.code,
              label: `${a.code} - ${a.name}`,
            })));
          }
        }
      } else {
        // Fallback to chart of accounts
        const coaRes = await api('/api/accounting/accounts?category=asset');
        if (coaRes.ok) {
          const coaData = await coaRes.json();
          const items = coaData.items || [];
          // Filter for cash/bank accounts by code pattern
          const cashBankAccounts = items.filter(a => 
            a.code?.startsWith('1-11') || 
            a.code?.startsWith('1-12') ||
            a.name?.toLowerCase().includes('kas') ||
            a.name?.toLowerCase().includes('bank')
          );
          setBanks(cashBankAccounts.map(a => ({
            value: a.id || a.code,
            label: `${a.code} - ${a.name}`,
          })));
        }
      }
    } catch (err) {
      console.error('Error loading banks:', err);
      // Set default accounts if all else fails
      setBanks([
        { value: '1-1100', label: '1-1100 - Kas' },
        { value: '1-1200', label: '1-1200 - Bank' },
      ]);
    } finally {
      setLoadingBanks(false);
    }
  }, [api]);
  
  const loadPayables = async (supplierId) => {
    if (!supplierId) {
      setPayables([]);
      return;
    }
    setLoadingPayables(true);
    try {
      const res = await api(`/api/ap/supplier/${supplierId}?include_paid=no`);
      if (res.ok) {
        const data = await res.json();
        const outstandingItems = (data.items || []).filter(ap => 
          (ap.outstanding_amount || 0) > 0 &&
          ['open', 'partial', 'overdue'].includes(ap.status)
        );
        setPayables(outstandingItems);
      } else {
        const res2 = await api(`/api/ap/list?supplier_id=${supplierId}`);
        if (res2.ok) {
          const data2 = await res2.json();
          const outstandingItems = (data2.items || []).filter(ap => 
            (ap.outstanding_amount || 0) > 0 &&
            ['open', 'partial', 'overdue'].includes(ap.status)
          );
          setPayables(outstandingItems);
        }
      }
    } catch (err) {
      console.error('Error loading payables:', err);
      setPayables([]);
    } finally {
      setLoadingPayables(false);
    }
  };

  useEffect(() => {
    loadPayments();
    loadBanks();
  }, [loadPayments, loadBanks]);
  
  const handleSupplierChange = (supplierId) => {
    setSelectedSupplier(supplierId);
    setFormData(prev => ({ ...prev, ap_id: '', amount: 0 }));
    loadPayables(supplierId);
  };
  
  const handleAPSelect = (ap) => {
    setFormData(prev => ({
      ...prev,
      ap_id: ap.id,
      amount: ap.outstanding_amount || 0,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (modalMode === 'create') {
      if (!formData.ap_id) {
        toast.error('Pilih hutang yang akan dibayar');
        return;
      }
    }
    if (formData.amount <= 0) {
      toast.error('Masukkan jumlah pembayaran');
      return;
    }
    
    setActionLoading(true);
    try {
      let res;
      if (modalMode === 'create') {
        // Create new payment
        const payload = {
          amount: formData.amount,
          payment_method: formData.payment_method,
          bank_account_id: formData.bank_account_id,
          reference_no: formData.reference_no,
          notes: formData.notes,
        };
        res = await api(`/api/ap/${formData.ap_id}/payment`, {
          method: 'POST',
          body: JSON.stringify(payload)
        });
      } else if (modalMode === 'edit') {
        // Update existing payment
        const payload = {
          amount: formData.amount,
          payment_method: formData.payment_method,
          bank_account_id: formData.bank_account_id,
          reference_no: formData.reference_no,
          notes: formData.notes,
        };
        res = await api(`/api/ap/payments/${selectedPayment.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload)
        });
      }
      
      if (res.ok) {
        const result = await res.json();
        toast.success(modalMode === 'create' 
          ? `Pembayaran berhasil dicatat. No: ${result.payment_no || ''}`
          : 'Pembayaran berhasil diupdate'
        );
        setShowModal(false);
        resetForm();
        loadPayments();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menyimpan pembayaran');
      }
    } catch (err) {
      console.error(err);
      toast.error('Gagal menyimpan pembayaran');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEdit = (payment) => {
    if (payment.status === 'posted') {
      toast.error('Pembayaran POSTED tidak dapat diedit. Gunakan Reversal.');
      return;
    }
    if (payment.status === 'reversed' || payment.status === 'deleted') {
      toast.error('Pembayaran ini tidak dapat diedit');
      return;
    }
    setSelectedPayment(payment);
    setFormData({
      ap_id: payment.ap_id || '',
      amount: payment.amount || 0,
      payment_method: payment.payment_method || 'transfer',
      bank_account_id: payment.bank_account_id || '',
      reference_no: payment.reference_no || '',
      notes: payment.notes || ''
    });
    setModalMode('edit');
    setShowModal(true);
  };

  const handleDelete = async () => {
    if (!selectedPayment) return;
    
    setActionLoading(true);
    try {
      const res = await api(`/api/ap/payments/${selectedPayment.id}`, {
        method: 'DELETE'
      });
      
      if (res.ok) {
        toast.success('Pembayaran berhasil dihapus');
        setShowDeleteConfirm(false);
        setSelectedPayment(null);
        loadPayments();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menghapus pembayaran');
      }
    } catch (err) {
      console.error(err);
      toast.error('Gagal menghapus pembayaran');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReversal = async () => {
    if (!selectedPayment) return;
    
    setActionLoading(true);
    try {
      const res = await api(`/api/ap/payments/${selectedPayment.id}/reversal`, {
        method: 'POST'
      });
      
      if (res.ok) {
        const result = await res.json();
        toast.success(`Pembayaran berhasil di-reverse. Jurnal: ${result.reversal_journal_no || ''}`);
        setShowReversalConfirm(false);
        setSelectedPayment(null);
        loadPayments();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal melakukan reversal');
      }
    } catch (err) {
      console.error(err);
      toast.error('Gagal melakukan reversal');
    } finally {
      setActionLoading(false);
    }
  };

  const openDeleteConfirm = (payment) => {
    if (payment.status === 'posted') {
      toast.error('Pembayaran POSTED tidak dapat dihapus. Gunakan Reversal.');
      return;
    }
    setSelectedPayment(payment);
    setShowDeleteConfirm(true);
  };

  const openReversalConfirm = (payment) => {
    if (payment.status !== 'posted') {
      toast.error('Hanya pembayaran POSTED yang dapat di-reverse');
      return;
    }
    setSelectedPayment(payment);
    setShowReversalConfirm(true);
  };

  const resetForm = () => {
    setFormData({ ap_id: '', amount: 0, payment_method: 'transfer', bank_account_id: '', reference_no: '', notes: '' });
    setSelectedSupplier('');
    setPayables([]);
    setSelectedPayment(null);
    setModalMode('create');
  };

  const openCreateModal = () => {
    resetForm();
    setShowModal(true);
  };

  return (
    <div className="space-y-4" data-testid="purchase-payments-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Pembayaran Hutang</h1>
          <p className="text-gray-400 text-sm">Kelola pembayaran ke supplier</p>
        </div>
        <button 
          onClick={openCreateModal}
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2"
          data-testid="btn-add-payment"
        >
          <Plus className="h-4 w-4" /> Tambah Pembayaran
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
            data-testid="search-payment"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="payments-table">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. PEMBAYARAN</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. HUTANG</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">SUPPLIER</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">JUMLAH</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">METODE</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : payments.length === 0 ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Belum ada data pembayaran</td></tr>
              ) : payments.map(payment => (
                <tr key={payment.id} className="hover:bg-red-900/10" data-testid={`payment-row-${payment.id}`}>
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">
                    {payment.payment_no || payment.payment_number || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {payment.payment_date || (payment.created_at ? new Date(payment.created_at).toLocaleDateString('id-ID') : '-')}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300">{payment.ap_no || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-200">{payment.supplier_name || '-'}</td>
                  <td className="px-4 py-3 text-sm text-right text-green-400 font-medium">
                    {formatRupiah(payment.amount)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-1 bg-blue-600/20 text-blue-400 rounded text-xs">
                      {payment.payment_method === 'transfer' ? 'Transfer' : 
                       payment.payment_method === 'cash' ? 'Tunai' : 
                       payment.payment_method === 'check' || payment.payment_method === 'giro' ? 'Cek/Giro' : 
                       payment.payment_method || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge status={payment.status || 'posted'} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {/* Edit - only for draft */}
                      {payment.status === 'draft' && (
                        <button
                          onClick={() => handleEdit(payment)}
                          className="p-1.5 text-amber-400 hover:bg-amber-600/20 rounded transition-colors"
                          title="Edit"
                          data-testid={`btn-edit-${payment.id}`}
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                      )}
                      
                      {/* Delete - only for draft */}
                      {payment.status === 'draft' && (
                        <button
                          onClick={() => openDeleteConfirm(payment)}
                          className="p-1.5 text-red-400 hover:bg-red-600/20 rounded transition-colors"
                          title="Hapus"
                          data-testid={`btn-delete-${payment.id}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                      
                      {/* Reversal - only for posted */}
                      {payment.status === 'posted' && (
                        <button
                          onClick={() => openReversalConfirm(payment)}
                          className="p-1.5 text-orange-400 hover:bg-orange-600/20 rounded transition-colors"
                          title="Reversal"
                          data-testid={`btn-reversal-${payment.id}`}
                        >
                          <RotateCcw className="h-4 w-4" />
                        </button>
                      )}
                      
                      {/* View detail always available */}
                      <button
                        onClick={() => {
                          setSelectedPayment(payment);
                          setModalMode('view');
                          setShowModal(true);
                        }}
                        className="p-1.5 text-gray-400 hover:bg-gray-600/20 rounded transition-colors"
                        title="Lihat Detail"
                        data-testid={`btn-view-${payment.id}`}
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create/Edit Payment Modal */}
      {showModal && modalMode !== 'view' && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">
                {modalMode === 'create' ? 'Tambah Pembayaran Hutang' : 'Edit Pembayaran'}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5 text-gray-400" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              {modalMode === 'create' && (
                <>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Supplier *</label>
                    <SearchableSelect
                      options={supplierOptions}
                      value={selectedSupplier}
                      onValueChange={handleSupplierChange}
                      placeholder="Ketik nama supplier..."
                      searchPlaceholder="Cari supplier..."
                      data-testid="supplier-select"
                    />
                  </div>
                  
                  {/* Outstanding Payables */}
                  {selectedSupplier && (
                    <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
                      <p className="text-sm text-gray-400 mb-2 flex items-center gap-2">
                        <Building2 className="h-4 w-4" />
                        Hutang Belum Lunas:
                        {loadingPayables && <Loader2 className="h-4 w-4 animate-spin" />}
                      </p>
                      {payables.length === 0 ? (
                        <p className="text-xs text-gray-500">Tidak ada hutang outstanding untuk supplier ini</p>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {payables.map(ap => (
                            <button
                              type="button"
                              key={ap.id}
                              onClick={() => handleAPSelect(ap)}
                              className={`px-3 py-1 text-xs rounded transition-colors ${
                                formData.ap_id === ap.id
                                  ? 'bg-green-700/50 text-green-300 ring-1 ring-green-500'
                                  : 'bg-gray-700 hover:bg-gray-600 text-amber-100'
                              }`}
                              data-testid={`select-ap-${ap.id}`}
                            >
                              {ap.ap_no} - {formatRupiah(ap.outstanding_amount)}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
              
              {modalMode === 'edit' && selectedPayment && (
                <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
                  <p className="text-sm text-gray-400">No. Pembayaran</p>
                  <p className="text-amber-300 font-mono">{selectedPayment.payment_no}</p>
                </div>
              )}
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah Pembayaran (Rp) *</label>
                <input 
                  type="number" 
                  min="0" 
                  value={formData.amount} 
                  onChange={(e) => setFormData({ ...formData, amount: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100" 
                  required 
                  data-testid="input-amount"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Metode Pembayaran</label>
                  <SearchableEnumSelect
                    options={paymentMethodOptions}
                    value={formData.payment_method}
                    onValueChange={(val) => setFormData({ ...formData, payment_method: val })}
                    placeholder="Pilih metode..."
                    data-testid="payment-method-select"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Bank/Kas</label>
                  {loadingBanks ? (
                    <div className="flex items-center gap-2 px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-500">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Memuat akun...</span>
                    </div>
                  ) : banks.length === 0 ? (
                    <div className="px-3 py-2 bg-yellow-900/20 border border-yellow-700/30 rounded-lg text-yellow-400 text-sm">
                      Tidak ada akun Kas/Bank
                    </div>
                  ) : (
                    <SearchableSelect
                      options={banks}
                      value={formData.bank_account_id}
                      onValueChange={(val) => setFormData({ ...formData, bank_account_id: val })}
                      placeholder="Pilih akun..."
                      searchPlaceholder="Cari akun..."
                      data-testid="bank-select"
                    />
                  )}
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Referensi/No. Bukti</label>
                <input 
                  type="text" 
                  value={formData.reference_no} 
                  onChange={(e) => setFormData({ ...formData, reference_no: e.target.value })}
                  placeholder="No. transfer, no. cek, dll"
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100" 
                  data-testid="input-reference"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea 
                  value={formData.notes} 
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100" 
                  rows={2} 
                  data-testid="input-notes"
                />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button 
                  type="button" 
                  onClick={() => setShowModal(false)} 
                  className="px-4 py-2 border border-red-900/30 rounded-lg text-amber-100"
                >
                  Batal
                </button>
                <button 
                  type="submit" 
                  disabled={actionLoading}
                  className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2 disabled:opacity-50" 
                  data-testid="submit-payment"
                >
                  {actionLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                  {modalMode === 'create' ? 'Simpan' : 'Update'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Detail Modal */}
      {showModal && modalMode === 'view' && selectedPayment && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">Detail Pembayaran</h2>
              <button onClick={() => { setShowModal(false); setSelectedPayment(null); }} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5 text-gray-400" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">No. Pembayaran</p>
                  <p className="text-amber-300 font-mono">{selectedPayment.payment_no || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  <StatusBadge status={selectedPayment.status || 'posted'} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Tanggal</p>
                  <p className="text-gray-200">{selectedPayment.payment_date || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">No. Hutang</p>
                  <p className="text-gray-200">{selectedPayment.ap_no || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Supplier</p>
                  <p className="text-gray-200">{selectedPayment.supplier_name || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Jumlah</p>
                  <p className="text-green-400 font-bold">{formatRupiah(selectedPayment.amount)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Metode</p>
                  <p className="text-gray-200">{selectedPayment.payment_method || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Referensi</p>
                  <p className="text-gray-200">{selectedPayment.reference_no || '-'}</p>
                </div>
              </div>
              {selectedPayment.notes && (
                <div>
                  <p className="text-sm text-gray-500">Catatan</p>
                  <p className="text-gray-200">{selectedPayment.notes}</p>
                </div>
              )}
              {selectedPayment.journal_id && (
                <div>
                  <p className="text-sm text-gray-500">No. Jurnal</p>
                  <p className="text-amber-300 font-mono">{selectedPayment.journal_id}</p>
                </div>
              )}
              <div className="flex justify-end pt-4 border-t border-red-900/30">
                <button 
                  onClick={() => { setShowModal(false); setSelectedPayment(null); }} 
                  className="px-4 py-2 bg-gray-700 text-white rounded-lg"
                >
                  Tutup
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && selectedPayment && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-4 border-b border-red-900/30">
              <h2 className="text-lg font-semibold text-amber-100 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-400" />
                Konfirmasi Hapus
              </h2>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-gray-300">
                Apakah Anda yakin ingin menghapus pembayaran ini?
              </p>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-sm text-gray-400">No. Pembayaran</p>
                <p className="text-amber-300 font-mono">{selectedPayment.payment_no}</p>
                <p className="text-sm text-gray-400 mt-2">Jumlah</p>
                <p className="text-green-400 font-bold">{formatRupiah(selectedPayment.amount)}</p>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button 
                  onClick={() => { setShowDeleteConfirm(false); setSelectedPayment(null); }}
                  className="px-4 py-2 border border-red-900/30 rounded-lg text-amber-100"
                >
                  Batal
                </button>
                <button 
                  onClick={handleDelete}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg flex items-center gap-2 disabled:opacity-50"
                  data-testid="confirm-delete"
                >
                  {actionLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                  Hapus
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reversal Confirmation Modal */}
      {showReversalConfirm && selectedPayment && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-4 border-b border-red-900/30">
              <h2 className="text-lg font-semibold text-amber-100 flex items-center gap-2">
                <RotateCcw className="h-5 w-5 text-orange-400" />
                Konfirmasi Reversal
              </h2>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-gray-300">
                Reversal akan membatalkan pembayaran ini dan membuat jurnal pembalik. Lanjutkan?
              </p>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-sm text-gray-400">No. Pembayaran</p>
                <p className="text-amber-300 font-mono">{selectedPayment.payment_no}</p>
                <p className="text-sm text-gray-400 mt-2">Jumlah</p>
                <p className="text-green-400 font-bold">{formatRupiah(selectedPayment.amount)}</p>
              </div>
              <div className="bg-orange-900/20 border border-orange-700/30 rounded-lg p-3 text-sm text-orange-300">
                <strong>Perhatian:</strong> Reversal akan menambah kembali saldo hutang dan membuat jurnal pembalik.
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button 
                  onClick={() => { setShowReversalConfirm(false); setSelectedPayment(null); }}
                  className="px-4 py-2 border border-red-900/30 rounded-lg text-amber-100"
                >
                  Batal
                </button>
                <button 
                  onClick={handleReversal}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-orange-600 text-white rounded-lg flex items-center gap-2 disabled:opacity-50"
                  data-testid="confirm-reversal"
                >
                  {actionLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                  Reversal
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PurchasePayments;
