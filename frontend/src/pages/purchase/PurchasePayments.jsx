import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Loader2, X, Building2 } from 'lucide-react';
import { toast } from 'sonner';
import { SearchableSelect } from '../../components/ui/searchable-select';
import { SearchableEnumSelect } from '../../components/ui/searchable-enum-select';
import { DatePickerWithDefault } from '../../components/ui/date-picker-default';
import { useSuppliers } from '../../hooks/useMasterData';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

// Payment method options
const paymentMethodOptions = [
  { value: 'transfer', label: 'Transfer Bank' },
  { value: 'cash', label: 'Tunai' },
  { value: 'check', label: 'Cek/Giro' },
];

const PurchasePayments = () => {
  const { api, token } = useAuth();
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  
  // Use custom hook for suppliers
  const { data: supplierOptions, loading: suppliersLoading } = useSuppliers(token);
  const [payables, setPayables] = useState([]);
  const [loadingPayables, setLoadingPayables] = useState(false);
  const [banks, setBanks] = useState([]);
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
      // Load AP payments history from ap_payments collection
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

  const loadBanks = useCallback(async () => {
    try {
      const bankRes = await api('/api/accounting/coa?type=kas');
      if (bankRes.ok) {
        const data = await bankRes.json();
        const accs = data.accounts || data.items || data || [];
        setBanks(accs.map(a => ({
          value: a.id || a.code,
          label: `${a.code} - ${a.name}`,
        })));
      }
    } catch (err) {
      console.error('Error loading banks');
    }
  }, [api]);
  
  const loadPayables = async (supplierId) => {
    if (!supplierId) {
      setPayables([]);
      return;
    }
    setLoadingPayables(true);
    try {
      // Get AP with outstanding > 0 for this supplier
      const res = await api(`/api/ap/supplier/${supplierId}?include_paid=no`);
      if (res.ok) {
        const data = await res.json();
        // Filter to only show items with outstanding_amount > 0
        const outstandingItems = (data.items || []).filter(ap => 
          (ap.outstanding_amount || 0) > 0 &&
          ['open', 'partial', 'overdue'].includes(ap.status)
        );
        setPayables(outstandingItems);
      } else {
        // Fallback: try the list endpoint
        const res2 = await api(`/api/ap?supplier_id=${supplierId}`);
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
    if (!formData.ap_id) {
      toast.error('Pilih hutang yang akan dibayar');
      return;
    }
    if (formData.amount <= 0) {
      toast.error('Masukkan jumlah pembayaran');
      return;
    }
    
    try {
      // Call the correct endpoint: POST /api/ap/{ap_id}/payment
      const payload = {
        amount: formData.amount,
        payment_method: formData.payment_method,
        bank_account_id: formData.bank_account_id,
        reference_no: formData.reference_no,
        notes: formData.notes,
      };
      
      const res = await api(`/api/ap/${formData.ap_id}/payment`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const result = await res.json();
        toast.success(`Pembayaran berhasil dicatat. No: ${result.payment_no || ''}`);
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
    }
  };

  const resetForm = () => {
    setFormData({ ap_id: '', amount: 0, payment_method: 'transfer', bank_account_id: '', reference_no: '', notes: '' });
    setSelectedSupplier('');
    setPayables([]);
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
              <h2 className="text-lg font-semibold text-amber-100">Catat Pembayaran Hutang</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
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
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah Pembayaran (Rp) *</label>
                <input type="number" min="0" value={formData.amount} 
                  onChange={(e) => setFormData({ ...formData, amount: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100" required />
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
                  <SearchableSelect
                    options={banks}
                    value={formData.bank_account_id}
                    onValueChange={(val) => setFormData({ ...formData, bank_account_id: val })}
                    placeholder="Pilih akun..."
                    searchPlaceholder="Cari akun..."
                    data-testid="bank-select"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Referensi/No. Bukti</label>
                <input type="text" value={formData.reference_no} 
                  onChange={(e) => setFormData({ ...formData, reference_no: e.target.value })}
                  placeholder="No. transfer, no. cek, dll"
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-amber-100" rows={2} />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg text-amber-100">Batal</button>
                <button type="submit" className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg" data-testid="submit-payment">Simpan</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PurchasePayments;
