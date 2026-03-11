import React, { useState, useEffect } from 'react';
import { ClipboardList, Search, Filter, Download, ArrowUpDown, Package } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MasterStockCards = () => {
  
  const [products, setProducts] = useState([]);
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [movementType, setMovementType] = useState('');

  useEffect(() => {
    fetchProducts();
  }, []);

  useEffect(() => {
    if (selectedProduct) {
      fetchMovements(selectedProduct);
    }
  }, [selectedProduct, dateFrom, dateTo, movementType]);

  const fetchProducts = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/api/products?limit=500`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProducts(res.data.items || res.data || []);
    } catch (err) {
      console.error('Error fetching products:', err);
    }
  };

  const fetchMovements = async (productId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = { product_id: productId };
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (movementType) params.type = movementType;
      
      const res = await axios.get(`${API_URL}/api/inventory/movements`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });
      
      // Calculate running balance
      let balance = 0;
      const movementsWithBalance = (res.data.items || res.data || [])
        .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
        .map(m => {
          balance += m.quantity || 0;
          return { ...m, running_balance: balance };
        })
        .reverse(); // Most recent first
      
      setMovements(movementsWithBalance);
    } catch (err) {
      console.error('Error fetching movements:', err);
      setMovements([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter(p =>
    p.name?.toLowerCase().includes(search.toLowerCase()) ||
    p.code?.toLowerCase().includes(search.toLowerCase())
  );

  const selectedProductData = products.find(p => p.id === selectedProduct);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('id-ID', {
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('id-ID').format(num || 0);
  };

  const getMovementTypeBadge = (type) => {
    const types = {
      'purchase_in': { label: 'Pembelian Masuk', color: 'bg-green-600' },
      'sales_out': { label: 'Penjualan', color: 'bg-red-600' },
      'sales_return_in': { label: 'Retur Jual', color: 'bg-blue-600' },
      'purchase_return_out': { label: 'Retur Beli', color: 'bg-orange-600' },
      'adjustment_in': { label: 'Penyesuaian +', color: 'bg-cyan-600' },
      'adjustment_out': { label: 'Penyesuaian -', color: 'bg-yellow-600' },
      'transfer_in': { label: 'Transfer Masuk', color: 'bg-purple-600' },
      'transfer_out': { label: 'Transfer Keluar', color: 'bg-pink-600' },
      'trade_in': { label: 'Tukar Tambah Masuk', color: 'bg-teal-600' },
      'trade_out': { label: 'Tukar Tambah Keluar', color: 'bg-rose-600' },
    };
    const t = types[type] || { label: type, color: 'bg-gray-600' };
    return <span className={`px-2 py-1 rounded text-xs ${t.color}`}>{t.label}</span>;
  };

  const handleExport = () => {
    if (!selectedProduct) {
      toast.info('Pilih produk terlebih dahulu');
      return;
    }
    
    const csvContent = [
      ['Tanggal', 'Jenis', 'Referensi', 'Masuk', 'Keluar', 'Saldo'],
      ...movements.map(m => [
        formatDate(m.created_at),
        m.type,
        m.reference || '-',
        m.quantity > 0 ? m.quantity : '',
        m.quantity < 0 ? Math.abs(m.quantity) : '',
        m.running_balance
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kartu-stok-${selectedProductData?.code || 'product'}.csv`;
    a.click();
  };

  return (
    <div className="p-6" data-testid="master-stock-cards">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <ClipboardList className="w-6 h-6 text-yellow-500" />
          Kartu Stok
        </h1>
        <Button onClick={handleExport} variant="outline" className="border-gray-600">
          <Download className="w-4 h-4 mr-2" /> Export CSV
        </Button>
      </div>

      {/* Product Selection */}
      <div className="bg-gray-800 rounded-lg p-4 mb-6 border border-gray-700">
        <div className="grid grid-cols-5 gap-4">
          <div className="col-span-2">
            <label className="text-gray-400 text-sm mb-1 block">Pilih Produk</label>
            <Select value={selectedProduct} onValueChange={setSelectedProduct}>
              <SelectTrigger className="bg-gray-900 border-gray-700">
                <SelectValue placeholder="Pilih produk untuk melihat kartu stok" />
              </SelectTrigger>
              <SelectContent>
                {filteredProducts.map(p => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.code} - {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-gray-400 text-sm mb-1 block">Dari Tanggal</label>
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="bg-gray-900 border-gray-700"
            />
          </div>
          <div>
            <label className="text-gray-400 text-sm mb-1 block">Sampai Tanggal</label>
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="bg-gray-900 border-gray-700"
            />
          </div>
          <div>
            <label className="text-gray-400 text-sm mb-1 block">Jenis Mutasi</label>
            <Select value={movementType || "all"} onValueChange={(v) => setMovementType(v === "all" ? "" : v)}>
              <SelectTrigger className="bg-gray-900 border-gray-700">
                <SelectValue placeholder="Semua" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua</SelectItem>
                <SelectItem value="purchase_in">Pembelian Masuk</SelectItem>
                <SelectItem value="sales_out">Penjualan</SelectItem>
                <SelectItem value="sales_return_in">Retur Jual</SelectItem>
                <SelectItem value="purchase_return_out">Retur Beli</SelectItem>
                <SelectItem value="adjustment_in">Penyesuaian +</SelectItem>
                <SelectItem value="adjustment_out">Penyesuaian -</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Product Info Card */}
      {selectedProductData && (
        <div className="bg-gray-800 rounded-lg p-4 mb-6 border border-gray-700">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gray-700 rounded-lg flex items-center justify-center">
              <Package className="w-8 h-8 text-gray-400" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-white">{selectedProductData.name}</h2>
              <p className="text-gray-400">{selectedProductData.code} | {selectedProductData.barcode || 'No barcode'}</p>
            </div>
            <div className="text-right">
              <p className="text-gray-400 text-sm">Stok Saat Ini</p>
              <p className="text-3xl font-bold text-yellow-400">{formatNumber(selectedProductData.stock || 0)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Stock Movements Table */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="p-4 border-b border-gray-700">
          <h2 className="font-semibold text-white">Mutasi Stok</h2>
        </div>
        <table className="w-full">
          <thead className="bg-gray-900 text-gray-400 text-sm">
            <tr>
              <th className="px-4 py-3 text-left">Tanggal</th>
              <th className="px-4 py-3 text-left">Jenis Transaksi</th>
              <th className="px-4 py-3 text-left">Referensi</th>
              <th className="px-4 py-3 text-right">Masuk</th>
              <th className="px-4 py-3 text-right">Keluar</th>
              <th className="px-4 py-3 text-right">Saldo</th>
            </tr>
          </thead>
          <tbody className="text-white">
            {!selectedProduct ? (
              <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">Pilih produk untuk melihat kartu stok</td></tr>
            ) : loading ? (
              <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">Memuat data...</td></tr>
            ) : movements.length === 0 ? (
              <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">Tidak ada mutasi stok</td></tr>
            ) : (
              movements.map((item, idx) => (
                <tr key={idx} className="border-t border-gray-700 hover:bg-gray-700/50">
                  <td className="px-4 py-3 text-gray-400">{formatDate(item.created_at)}</td>
                  <td className="px-4 py-3">{getMovementTypeBadge(item.type)}</td>
                  <td className="px-4 py-3 font-mono text-yellow-400">{item.reference || '-'}</td>
                  <td className="px-4 py-3 text-right text-green-400">
                    {item.quantity > 0 ? formatNumber(item.quantity) : '-'}
                  </td>
                  <td className="px-4 py-3 text-right text-red-400">
                    {item.quantity < 0 ? formatNumber(Math.abs(item.quantity)) : '-'}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold">{formatNumber(item.running_balance)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MasterStockCards;
