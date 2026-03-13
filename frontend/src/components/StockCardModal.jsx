import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { X, Loader2, TrendingUp, TrendingDown, Package, Calendar, FileText } from 'lucide-react';
import { toast } from 'sonner';

/**
 * StockCardModal - Modal Kartu Stok Standar ERP
 * 
 * Menampilkan history pergerakan stok dari collection stock_movements
 * sebagai Single Source of Truth (SSOT)
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Status modal terbuka
 * @param {Function} props.onClose - Handler tutup modal
 * @param {Object} props.item - Item yang akan ditampilkan kartu stoknya
 * @param {string} props.branchId - Filter cabang (optional)
 */
const StockCardModal = ({ isOpen, onClose, item, branchId = '' }) => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [movements, setMovements] = useState([]);
  const [summary, setSummary] = useState({ total_in: 0, total_out: 0, balance: 0 });
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState(branchId);
  const [dateRange, setDateRange] = useState({
    from: '',
    to: ''
  });

  // Load stock movements from SSOT (stock_movements collection)
  const loadStockMovements = useCallback(async () => {
    if (!item?.id) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams({ item_id: item.id });
      if (selectedBranch) params.append('branch_id', selectedBranch);
      if (dateRange.from) params.append('date_from', dateRange.from);
      if (dateRange.to) params.append('date_to', dateRange.to);
      
      // Try the new modal endpoint first
      const res = await api(`/api/inventory/stock-card-modal?${params}`);
      if (res.ok) {
        const data = await res.json();
        setMovements(data.movements || []);
        setSummary({
          total_in: data.total_in || 0,
          total_out: data.total_out || 0,
          balance: data.balance || 0
        });
      } else {
        // Fallback: try original endpoint with current month/year
        const now = new Date();
        const fallbackParams = new URLSearchParams({ 
          item_id: item.id,
          month: now.getMonth() + 1,
          year: now.getFullYear()
        });
        if (selectedBranch) fallbackParams.append('branch_id', selectedBranch);
        
        const fallbackRes = await api(`/api/inventory/stock-card?${fallbackParams}`);
        if (fallbackRes.ok) {
          const data = await fallbackRes.json();
          // Transform old format to new format
          const mvmts = (data.movements || []).map(m => ({
            id: m.id,
            created_at: m.tanggal,
            reference_number: m.no_transaksi,
            transaction_type: m.jenis || 'other',
            branch_name: m.cabang || '-',
            quantity: (m.masuk || 0) - (m.keluar || 0),
            notes: m.keterangan || ''
          }));
          
          setMovements(mvmts);
          setSummary({
            total_in: data.total_masuk || 0,
            total_out: data.total_keluar || 0,
            balance: data.closing_balance || 0
          });
        }
      }
    } catch (err) {
      console.error('Error loading stock movements:', err);
      toast.error('Gagal memuat kartu stok');
    } finally {
      setLoading(false);
    }
  }, [api, item?.id, selectedBranch, dateRange]);

  // Load branches for filter
  const loadBranches = useCallback(async () => {
    try {
      const res = await api('/api/global-map/branches');
      if (res.ok) {
        const data = await res.json();
        setBranches(data.branches || []);
      }
    } catch (err) {
      console.error('Error loading branches');
    }
  }, [api]);

  useEffect(() => {
    if (isOpen && item) {
      loadStockMovements();
      loadBranches();
    }
  }, [isOpen, item, loadStockMovements, loadBranches]);

  // Get transaction type label and style
  const getTransactionStyle = (type) => {
    const types = {
      'purchase': { label: 'Pembelian', color: 'bg-green-900/30 text-green-400', icon: TrendingUp },
      'purchase_receive': { label: 'Terima Barang', color: 'bg-green-900/30 text-green-400', icon: TrendingUp },
      'sales': { label: 'Penjualan', color: 'bg-red-900/30 text-red-400', icon: TrendingDown },
      'pos': { label: 'POS', color: 'bg-red-900/30 text-red-400', icon: TrendingDown },
      'transfer_in': { label: 'Transfer Masuk', color: 'bg-blue-900/30 text-blue-400', icon: TrendingUp },
      'transfer_out': { label: 'Transfer Keluar', color: 'bg-orange-900/30 text-orange-400', icon: TrendingDown },
      'adjustment_in': { label: 'Penyesuaian +', color: 'bg-cyan-900/30 text-cyan-400', icon: TrendingUp },
      'adjustment_out': { label: 'Penyesuaian -', color: 'bg-amber-900/30 text-amber-400', icon: TrendingDown },
      'opname': { label: 'Stock Opname', color: 'bg-purple-900/30 text-purple-400', icon: Package },
      'return_in': { label: 'Retur Masuk', color: 'bg-teal-900/30 text-teal-400', icon: TrendingUp },
      'return_out': { label: 'Retur Keluar', color: 'bg-rose-900/30 text-rose-400', icon: TrendingDown },
      'initial': { label: 'Stok Awal', color: 'bg-gray-900/30 text-gray-400', icon: Package },
    };
    return types[type] || { label: type || 'Lainnya', color: 'bg-gray-900/30 text-gray-400', icon: FileText };
  };

  // Format date
  const formatDate = (date) => {
    if (!date) return '-';
    return new Date(date).toLocaleDateString('id-ID', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Calculate running balance
  const getRunningBalance = (movements) => {
    let balance = 0;
    return movements.map(m => {
      balance += m.quantity;
      return { ...m, running_balance: balance };
    });
  };

  if (!isOpen) return null;

  const movementsWithBalance = getRunningBalance(movements);

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-red-900/30 bg-red-900/10">
          <div className="flex items-center gap-3">
            <Package className="h-5 w-5 text-amber-400" />
            <div>
              <h3 className="text-lg font-bold text-amber-100">Kartu Stok</h3>
              <p className="text-sm text-gray-400">
                {item?.code} - {item?.name}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-red-900/30 rounded-lg transition-colors"
            data-testid="btn-close-stock-card"
          >
            <X className="h-5 w-5 text-gray-400" />
          </button>
        </div>

        {/* Filters */}
        <div className="px-4 py-3 border-b border-red-900/30 bg-[#0a0608]/50">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-400">Cabang:</label>
              <select
                value={selectedBranch}
                onChange={(e) => setSelectedBranch(e.target.value)}
                className="px-2 py-1 text-sm bg-[#0a0608] border border-red-900/30 rounded text-gray-200"
                data-testid="filter-branch-stock-card"
              >
                <option value="">Semua Cabang</option>
                {branches.map(b => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-400">Dari:</label>
              <input
                type="date"
                value={dateRange.from}
                onChange={(e) => setDateRange(prev => ({ ...prev, from: e.target.value }))}
                className="px-2 py-1 text-sm bg-[#0a0608] border border-red-900/30 rounded text-gray-200"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-400">Sampai:</label>
              <input
                type="date"
                value={dateRange.to}
                onChange={(e) => setDateRange(prev => ({ ...prev, to: e.target.value }))}
                className="px-2 py-1 text-sm bg-[#0a0608] border border-red-900/30 rounded text-gray-200"
              />
            </div>
            <button
              onClick={loadStockMovements}
              className="px-3 py-1 bg-amber-600 text-white text-sm rounded hover:bg-amber-700"
            >
              Filter
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-3 px-4 py-3 border-b border-red-900/30">
          <div className="bg-green-900/20 border border-green-900/30 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-2 text-green-400 mb-1">
              <TrendingUp className="h-4 w-4" />
              <span className="text-xs font-medium">Total Masuk</span>
            </div>
            <p className="text-xl font-bold text-green-300">{summary.total_in.toLocaleString('id-ID')}</p>
          </div>
          <div className="bg-red-900/20 border border-red-900/30 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-2 text-red-400 mb-1">
              <TrendingDown className="h-4 w-4" />
              <span className="text-xs font-medium">Total Keluar</span>
            </div>
            <p className="text-xl font-bold text-red-300">{summary.total_out.toLocaleString('id-ID')}</p>
          </div>
          <div className="bg-amber-900/20 border border-amber-900/30 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-2 text-amber-400 mb-1">
              <Package className="h-4 w-4" />
              <span className="text-xs font-medium">Saldo Akhir</span>
            </div>
            <p className="text-xl font-bold text-amber-300">{summary.balance.toLocaleString('id-ID')}</p>
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-red-900/20 sticky top-0">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-amber-200">NO. TRANSAKSI</th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-amber-200">JENIS TRANSAKSI</th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-amber-200">CABANG</th>
                <th className="px-3 py-2 text-right text-xs font-semibold text-amber-200">MASUK</th>
                <th className="px-3 py-2 text-right text-xs font-semibold text-amber-200">KELUAR</th>
                <th className="px-3 py-2 text-right text-xs font-semibold text-amber-200">SALDO</th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-amber-200">CATATAN</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400 mb-2" />
                    <p className="text-gray-400 text-sm">Memuat kartu stok...</p>
                  </td>
                </tr>
              ) : movementsWithBalance.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-gray-400">
                    Belum ada pergerakan stok untuk item ini
                  </td>
                </tr>
              ) : (
                movementsWithBalance.map((m, idx) => {
                  const txStyle = getTransactionStyle(m.transaction_type);
                  const TxIcon = txStyle.icon;
                  const qtyIn = m.quantity > 0 ? m.quantity : 0;
                  const qtyOut = m.quantity < 0 ? Math.abs(m.quantity) : 0;
                  
                  return (
                    <tr 
                      key={m.id || idx} 
                      className={`hover:bg-red-900/10 ${idx % 2 === 0 ? 'bg-[#0a0608]/30' : ''}`}
                    >
                      <td className="px-3 py-2 text-gray-300 whitespace-nowrap">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3 text-gray-500" />
                          {formatDate(m.created_at || m.timestamp)}
                        </div>
                      </td>
                      <td className="px-3 py-2 font-mono text-amber-400 text-xs">
                        {m.reference_number || m.ref_id || '-'}
                      </td>
                      <td className="px-3 py-2">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${txStyle.color}`}>
                          <TxIcon className="h-3 w-3" />
                          {txStyle.label}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-gray-400 text-xs">
                        {m.branch_name || '-'}
                      </td>
                      <td className="px-3 py-2 text-right">
                        {qtyIn > 0 ? (
                          <span className="text-green-400 font-medium">+{qtyIn.toLocaleString('id-ID')}</span>
                        ) : (
                          <span className="text-gray-600">-</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right">
                        {qtyOut > 0 ? (
                          <span className="text-red-400 font-medium">-{qtyOut.toLocaleString('id-ID')}</span>
                        ) : (
                          <span className="text-gray-600">-</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <span className={`font-bold ${m.running_balance >= 0 ? 'text-amber-400' : 'text-red-400'}`}>
                          {m.running_balance.toLocaleString('id-ID')}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-gray-500 text-xs max-w-[150px] truncate" title={m.notes}>
                        {m.notes || '-'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-red-900/30 bg-[#0a0608]/50 flex items-center justify-between">
          <div className="text-xs text-gray-500">
            Data dari <span className="text-amber-400 font-medium">stock_movements</span> (Single Source of Truth)
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
};

export default StockCardModal;
