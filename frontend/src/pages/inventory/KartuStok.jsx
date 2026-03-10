import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  FileText, Search, Calendar, Building2, Loader2, Download, 
  ArrowUpCircle, ArrowDownCircle, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';

const KartuStok = () => {
  const { api } = useAuth();
  
  // Filter states
  const [itemSearch, setItemSearch] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedBranch, setSelectedBranch] = useState('');
  const [branches, setBranches] = useState([]);
  
  // Data states
  const [stockCard, setStockCard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);

  // Load branches on mount
  useEffect(() => {
    loadBranches();
  }, []);

  const loadBranches = async () => {
    try {
      const res = await api('/api/global-map/branches');
      if (res.ok) {
        const data = await res.json();
        setBranches(data.branches || []);
      }
    } catch (err) {
      console.error('Failed to load branches:', err);
    }
  };

  // Search items
  const searchItems = async (query) => {
    if (!query || query.length < 1) {
      setSearchResults([]);
      return;
    }
    
    setSearching(true);
    try {
      const res = await api(`/api/inventory/stock-card/items-search?q=${encodeURIComponent(query)}`);
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.items || []);
        setShowDropdown(true);
      }
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setSearching(false);
    }
  };

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (itemSearch && !selectedItem) {
        searchItems(itemSearch);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [itemSearch]);

  // Select item from dropdown
  const selectItem = (item) => {
    setSelectedItem(item);
    setItemSearch(`${item.code} - ${item.name}`);
    setShowDropdown(false);
    setSearchResults([]);
  };

  // Clear selected item
  const clearItem = () => {
    setSelectedItem(null);
    setItemSearch('');
    setStockCard(null);
  };

  // Process - Load stock card
  const processStockCard = async () => {
    if (!selectedItem) {
      toast.error('Pilih item terlebih dahulu');
      return;
    }
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        item_id: selectedItem.id,
        month: selectedMonth,
        year: selectedYear
      });
      if (selectedBranch) {
        params.append('branch_id', selectedBranch);
      }
      
      const res = await api(`/api/inventory/stock-card?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setStockCard(data);
        toast.success(`Kartu Stok ${data.item.code} berhasil dimuat`);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal memuat kartu stok');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    } finally {
      setLoading(false);
    }
  };

  // Create test data
  const createTestData = async () => {
    if (!selectedItem || !selectedBranch) {
      toast.error('Pilih item dan cabang terlebih dahulu');
      return;
    }
    
    try {
      const res = await api(`/api/inventory/stock-card/create-test-data?item_id=${selectedItem.id}&branch_id=${selectedBranch}`, {
        method: 'POST'
      });
      if (res.ok) {
        toast.success('Data test berhasil dibuat');
        processStockCard();
      }
    } catch (err) {
      toast.error('Gagal membuat data test');
    }
  };

  // Month options
  const months = [
    { value: 1, label: 'Januari' },
    { value: 2, label: 'Februari' },
    { value: 3, label: 'Maret' },
    { value: 4, label: 'April' },
    { value: 5, label: 'Mei' },
    { value: 6, label: 'Juni' },
    { value: 7, label: 'Juli' },
    { value: 8, label: 'Agustus' },
    { value: 9, label: 'September' },
    { value: 10, label: 'Oktober' },
    { value: 11, label: 'November' },
    { value: 12, label: 'Desember' }
  ];

  // Year options (last 5 years)
  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  // Format number
  const formatNumber = (num) => {
    return num?.toLocaleString('id-ID') || '0';
  };

  return (
    <div className="min-h-screen bg-[#0d0809] p-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <FileText className="h-6 w-6 text-amber-400" />
        <h1 className="text-xl font-bold text-amber-100">Kartu Stok</h1>
        <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">ERP Classic</span>
      </div>

      {/* Filter Area - ERP Style */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-lg p-4 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
          {/* Kode Item */}
          <div className="md:col-span-2 relative">
            <label className="block text-xs text-gray-400 mb-1">Kode Item</label>
            <div className="relative">
              <input
                type="text"
                value={itemSearch}
                onChange={(e) => {
                  setItemSearch(e.target.value);
                  if (selectedItem) {
                    setSelectedItem(null);
                  }
                }}
                placeholder="Cari kode / nama item..."
                className="w-full px-3 py-2 pr-10 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                data-testid="item-search"
              />
              <button
                onClick={() => searchItems(itemSearch)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-amber-400"
              >
                {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              </button>
            </div>
            
            {/* Dropdown Results */}
            {showDropdown && searchResults.length > 0 && (
              <div className="absolute z-50 w-full mt-1 bg-[#1a1214] border border-red-900/30 rounded shadow-lg max-h-60 overflow-y-auto">
                {searchResults.map(item => (
                  <button
                    key={item.id}
                    onClick={() => selectItem(item)}
                    className="w-full px-3 py-2 text-left hover:bg-red-900/20 border-b border-red-900/10 last:border-0"
                  >
                    <span className="text-amber-300 font-mono text-sm">{item.code}</span>
                    <span className="text-gray-400 text-sm ml-2">- {item.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Periode - Bulan */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Bulan</label>
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
              data-testid="select-month"
            >
              {months.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          {/* Periode - Tahun */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tahun</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
              data-testid="select-year"
            >
              {years.map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>

          {/* Cabang */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Cabang</label>
            <select
              value={selectedBranch}
              onChange={(e) => setSelectedBranch(e.target.value)}
              className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
              data-testid="select-branch"
            >
              <option value="">Semua Cabang</option>
              {branches.map(b => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={processStockCard}
            disabled={loading || !selectedItem}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 font-semibold"
            data-testid="btn-process"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            PROSES
          </button>
          <button
            onClick={clearItem}
            className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
          >
            Reset
          </button>
          {selectedItem && selectedBranch && (
            <button
              onClick={createTestData}
              className="px-4 py-2 bg-amber-600 text-white rounded hover:bg-amber-700 text-sm"
            >
              + Data Test
            </button>
          )}
        </div>
      </div>

      {/* Stock Card Table */}
      {stockCard && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-lg overflow-hidden">
          {/* Card Header */}
          <div className="px-4 py-3 bg-red-900/20 border-b border-red-900/30">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-amber-100">
                  Kartu Stok: {stockCard.item?.code} - {stockCard.item?.name}
                </h2>
                <p className="text-sm text-gray-400">
                  Periode: {stockCard.period} | Cabang: {stockCard.branch_name}
                </p>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-400">Saldo Akhir</div>
                <div className="text-2xl font-bold text-amber-400">{formatNumber(stockCard.closing_balance)}</div>
              </div>
            </div>
          </div>

          {/* Summary Row */}
          <div className="grid grid-cols-4 gap-4 px-4 py-3 bg-[#0a0608] border-b border-red-900/30">
            <div className="text-center">
              <div className="text-xs text-gray-500">Saldo Awal</div>
              <div className="text-lg font-semibold text-gray-300">{formatNumber(stockCard.opening_balance)}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500">Total Masuk</div>
              <div className="text-lg font-semibold text-green-400 flex items-center justify-center gap-1">
                <ArrowUpCircle className="h-4 w-4" />
                {formatNumber(stockCard.total_masuk)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500">Total Keluar</div>
              <div className="text-lg font-semibold text-red-400 flex items-center justify-center gap-1">
                <ArrowDownCircle className="h-4 w-4" />
                {formatNumber(stockCard.total_keluar)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500">Saldo Akhir</div>
              <div className="text-lg font-semibold text-amber-400">{formatNumber(stockCard.closing_balance)}</div>
            </div>
          </div>

          {/* Table - ERP Classic Style */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-gradient-to-r from-amber-900/40 to-red-900/40">
                <tr>
                  <th className="px-2 py-2 text-left text-amber-200 font-semibold border-r border-red-900/20">No Transaksi</th>
                  <th className="px-2 py-2 text-left text-amber-200 font-semibold border-r border-red-900/20">Kantor/Cabang</th>
                  <th className="px-2 py-2 text-left text-amber-200 font-semibold border-r border-red-900/20">Tanggal</th>
                  <th className="px-2 py-2 text-left text-amber-200 font-semibold border-r border-red-900/20">Tipe</th>
                  <th className="px-2 py-2 text-center text-amber-200 font-semibold border-r border-red-900/20">Baris</th>
                  <th className="px-2 py-2 text-left text-amber-200 font-semibold border-r border-red-900/20">Keterangan</th>
                  <th className="px-2 py-2 text-right text-green-300 font-semibold border-r border-red-900/20">Masuk</th>
                  <th className="px-2 py-2 text-right text-red-300 font-semibold border-r border-red-900/20">Keluar</th>
                  <th className="px-2 py-2 text-right text-amber-200 font-semibold border-r border-red-900/20">Saldo</th>
                  <th className="px-2 py-2 text-left text-amber-200 font-semibold">Supplier/Pelanggan</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/10">
                {stockCard.movements?.map((row, idx) => (
                  <tr 
                    key={idx} 
                    className={`hover:bg-red-900/10 ${idx === 0 ? 'bg-blue-900/20 font-semibold' : ''}`}
                  >
                    <td className="px-2 py-1.5 text-amber-300 font-mono border-r border-red-900/10">
                      {row.no_transaksi}
                    </td>
                    <td className="px-2 py-1.5 text-gray-300 border-r border-red-900/10">{row.cabang}</td>
                    <td className="px-2 py-1.5 text-gray-400 border-r border-red-900/10">{row.tanggal}</td>
                    <td className="px-2 py-1.5 border-r border-red-900/10">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        row.tipe === 'Saldo Awal' ? 'bg-blue-900/50 text-blue-300' :
                        row.tipe === 'Pembelian' ? 'bg-green-900/50 text-green-300' :
                        row.tipe === 'Penjualan' ? 'bg-red-900/50 text-red-300' :
                        row.tipe === 'Transfer Masuk' ? 'bg-cyan-900/50 text-cyan-300' :
                        row.tipe === 'Transfer Keluar' ? 'bg-orange-900/50 text-orange-300' :
                        row.tipe === 'Stok Masuk' ? 'bg-emerald-900/50 text-emerald-300' :
                        row.tipe === 'Stok Keluar' ? 'bg-pink-900/50 text-pink-300' :
                        row.tipe === 'Retur Penjualan' ? 'bg-purple-900/50 text-purple-300' :
                        row.tipe === 'Retur Pembelian' ? 'bg-amber-900/50 text-amber-300' :
                        'bg-gray-900/50 text-gray-300'
                      }`}>
                        {row.tipe}
                      </span>
                    </td>
                    <td className="px-2 py-1.5 text-center text-gray-500 border-r border-red-900/10">{row.baris}</td>
                    <td className="px-2 py-1.5 text-gray-400 border-r border-red-900/10 max-w-[200px] truncate">
                      {row.keterangan}
                    </td>
                    <td className="px-2 py-1.5 text-right font-mono border-r border-red-900/10">
                      {row.masuk > 0 ? (
                        <span className="text-green-400">{formatNumber(row.masuk)}</span>
                      ) : (
                        <span className="text-gray-600">-</span>
                      )}
                    </td>
                    <td className="px-2 py-1.5 text-right font-mono border-r border-red-900/10">
                      {row.keluar > 0 ? (
                        <span className="text-red-400">{formatNumber(row.keluar)}</span>
                      ) : (
                        <span className="text-gray-600">-</span>
                      )}
                    </td>
                    <td className="px-2 py-1.5 text-right font-mono font-semibold text-amber-300 border-r border-red-900/10">
                      {formatNumber(row.saldo)}
                    </td>
                    <td className="px-2 py-1.5 text-gray-400">{row.supplier_pelanggan}</td>
                  </tr>
                ))}
              </tbody>
              {/* Footer Totals */}
              <tfoot className="bg-gradient-to-r from-amber-900/30 to-red-900/30">
                <tr className="font-semibold">
                  <td colSpan="6" className="px-2 py-2 text-right text-amber-200 border-r border-red-900/20">
                    TOTAL
                  </td>
                  <td className="px-2 py-2 text-right text-green-400 font-mono border-r border-red-900/20">
                    {formatNumber(stockCard.total_masuk)}
                  </td>
                  <td className="px-2 py-2 text-right text-red-400 font-mono border-r border-red-900/20">
                    {formatNumber(stockCard.total_keluar)}
                  </td>
                  <td className="px-2 py-2 text-right text-amber-400 font-mono font-bold border-r border-red-900/20">
                    {formatNumber(stockCard.closing_balance)}
                  </td>
                  <td className="px-2 py-2"></td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Footer Info */}
          <div className="px-4 py-2 bg-[#0a0608] border-t border-red-900/30 text-xs text-gray-500">
            Total {stockCard.count} baris | Digenerate: {new Date().toLocaleString('id-ID')}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!stockCard && !loading && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-lg p-8 text-center">
          <FileText className="h-12 w-12 text-gray-600 mx-auto mb-3" />
          <h3 className="text-gray-400 mb-2">Belum Ada Data</h3>
          <p className="text-sm text-gray-500">
            Pilih item dan periode, lalu klik <strong>PROSES</strong> untuk menampilkan kartu stok.
          </p>
        </div>
      )}
    </div>
  );
};

export default KartuStok;
