import React, { useState, useEffect } from 'react';
import { Table, Search, Download, Upload, Edit2, Trash2, Save, X, Filter } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MasterDatasheet = () => {
  
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [editingCell, setEditingCell] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [selectedRows, setSelectedRows] = useState([]);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [brandFilter, setBrandFilter] = useState('');

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [productsRes, categoriesRes, brandsRes, unitsRes] = await Promise.all([
        axios.get(`${API_URL}/api/products?limit=500`, { headers }),
        axios.get(`${API_URL}/api/master/categories`, { headers }),
        axios.get(`${API_URL}/api/master/brands`, { headers }),
        axios.get(`${API_URL}/api/master/units`, { headers })
      ]);
      
      setProducts(productsRes.data.items || productsRes.data || []);
      setCategories(categoriesRes.data.items || categoriesRes.data || []);
      setBrands(brandsRes.data.items || brandsRes.data || []);
      setUnits(unitsRes.data.items || unitsRes.data || []);
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCellClick = (productId, field, value) => {
    setEditingCell({ productId, field });
    setEditValue(value || '');
  };

  const handleSaveCell = async () => {
    if (!editingCell) return;
    
    try {
      const token = localStorage.getItem('token');
      const { productId, field } = editingCell;
      
      let updateData = {};
      if (field === 'cost_price' || field === 'selling_price' || field === 'min_stock') {
        updateData[field] = parseFloat(editValue) || 0;
      } else {
        updateData[field] = editValue;
      }
      
      await axios.put(`${API_URL}/api/products/${productId}`, updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update local state
      setProducts(products.map(p => 
        p.id === productId ? { ...p, ...updateData } : p
      ));
      
      toast.success('Data berhasil diupdate');
      setEditingCell(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal update');
    }
  };

  const handleCancelEdit = () => {
    setEditingCell(null);
    setEditValue('');
  };

  const handleExport = () => {
    const csvContent = [
      ['Kode', 'Barcode', 'Nama', 'Kategori', 'Merk', 'Satuan', 'Harga Beli', 'Harga Jual', 'Stok', 'Min Stok'],
      ...filteredProducts.map(p => [
        p.code,
        p.barcode || '',
        p.name,
        p.category_name || '',
        p.brand_name || '',
        p.unit_name || '',
        p.cost_price || 0,
        p.selling_price || 0,
        p.stock || 0,
        p.min_stock || 0
      ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'datasheet-produk.csv';
    a.click();
    toast.success('Data berhasil diexport');
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv,.xlsx';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      toast.info('Import sedang dalam pengembangan');
    };
    input.click();
  };

  const toggleRowSelect = (id) => {
    setSelectedRows(prev => 
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    );
  };

  const filteredProducts = products.filter(p => {
    const matchesSearch = !search || 
      p.name?.toLowerCase().includes(search.toLowerCase()) ||
      p.code?.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = !categoryFilter || p.category_id === categoryFilter;
    const matchesBrand = !brandFilter || p.brand_id === brandFilter;
    return matchesSearch && matchesCategory && matchesBrand;
  });

  const formatCurrency = (num) => {
    return new Intl.NumberFormat('id-ID').format(num || 0);
  };

  const EditableCell = ({ productId, field, value, type = 'text' }) => {
    const isEditing = editingCell?.productId === productId && editingCell?.field === field;
    
    if (isEditing) {
      return (
        <div className="flex items-center gap-1">
          <Input
            type={type}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            className="h-7 text-xs bg-gray-900 border-gray-600 w-full"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSaveCell();
              if (e.key === 'Escape') handleCancelEdit();
            }}
          />
          <Button size="sm" variant="ghost" onClick={handleSaveCell} className="h-6 w-6 p-0">
            <Save className="w-3 h-3 text-green-400" />
          </Button>
          <Button size="sm" variant="ghost" onClick={handleCancelEdit} className="h-6 w-6 p-0">
            <X className="w-3 h-3 text-red-400" />
          </Button>
        </div>
      );
    }
    
    return (
      <span 
        className="cursor-pointer hover:bg-gray-700 px-2 py-1 rounded block"
        onClick={() => handleCellClick(productId, field, value)}
      >
        {type === 'number' ? formatCurrency(value) : (value || '-')}
      </span>
    );
  };

  return (
    <div className="p-6" data-testid="master-datasheet">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Table className="w-6 h-6 text-yellow-500" />
          Datasheet Produk
        </h1>
        <div className="flex gap-2">
          <Button onClick={handleImport} variant="outline" className="border-gray-600">
            <Upload className="w-4 h-4 mr-2" /> Import Excel
          </Button>
          <Button onClick={handleExport} variant="outline" className="border-gray-600">
            <Download className="w-4 h-4 mr-2" /> Export Excel
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-gray-800 rounded-lg p-4 mb-6 border border-gray-700">
        <div className="flex gap-4 items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Cari produk..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-gray-900 border-gray-700"
            />
          </div>
          <Select value={categoryFilter || "all"} onValueChange={(v) => setCategoryFilter(v === "all" ? "" : v)}>
            <SelectTrigger className="w-48 bg-gray-900 border-gray-700">
              <SelectValue placeholder="Semua Kategori" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Semua Kategori</SelectItem>
              {categories.map(c => (
                <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={brandFilter || "all"} onValueChange={(v) => setBrandFilter(v === "all" ? "" : v)}>
            <SelectTrigger className="w-48 bg-gray-900 border-gray-700">
              <SelectValue placeholder="Semua Merk" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Semua Merk</SelectItem>
              {brands.map(b => (
                <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="text-gray-400 text-sm">{filteredProducts.length} produk</span>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-3 mb-4">
        <p className="text-blue-300 text-sm">
          <strong>Tips:</strong> Klik pada sel untuk edit langsung. Tekan Enter untuk simpan, Escape untuk batal.
        </p>
      </div>

      {/* Datasheet Table */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-x-auto">
        <table className="w-full min-w-[1200px]">
          <thead className="bg-gray-900 text-gray-400 text-xs sticky top-0">
            <tr>
              <th className="px-2 py-3 text-center w-10">
                <input type="checkbox" className="w-4 h-4" />
              </th>
              <th className="px-2 py-3 text-left">Kode</th>
              <th className="px-2 py-3 text-left">Barcode</th>
              <th className="px-2 py-3 text-left w-64">Nama Produk</th>
              <th className="px-2 py-3 text-left">Kategori</th>
              <th className="px-2 py-3 text-left">Merk</th>
              <th className="px-2 py-3 text-left">Satuan</th>
              <th className="px-2 py-3 text-right">Harga Beli</th>
              <th className="px-2 py-3 text-right">Harga Jual</th>
              <th className="px-2 py-3 text-right">Stok</th>
              <th className="px-2 py-3 text-right">Min Stok</th>
            </tr>
          </thead>
          <tbody className="text-white text-sm">
            {loading ? (
              <tr><td colSpan="11" className="px-4 py-8 text-center text-gray-400">Memuat data...</td></tr>
            ) : filteredProducts.length === 0 ? (
              <tr><td colSpan="11" className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
            ) : (
              filteredProducts.slice(0, 100).map((item) => (
                <tr 
                  key={item.id} 
                  className={`border-t border-gray-700 hover:bg-gray-700/50 ${selectedRows.includes(item.id) ? 'bg-yellow-900/20' : ''}`}
                >
                  <td className="px-2 py-2 text-center">
                    <input 
                      type="checkbox" 
                      checked={selectedRows.includes(item.id)}
                      onChange={() => toggleRowSelect(item.id)}
                      className="w-4 h-4"
                    />
                  </td>
                  <td className="px-2 py-2 font-mono text-yellow-400 text-xs">{item.code}</td>
                  <td className="px-2 py-2">
                    <EditableCell productId={item.id} field="barcode" value={item.barcode} />
                  </td>
                  <td className="px-2 py-2">
                    <EditableCell productId={item.id} field="name" value={item.name} />
                  </td>
                  <td className="px-2 py-2 text-gray-400">{item.category_name || '-'}</td>
                  <td className="px-2 py-2 text-gray-400">{item.brand_name || '-'}</td>
                  <td className="px-2 py-2 text-gray-400">{item.unit_name || '-'}</td>
                  <td className="px-2 py-2 text-right">
                    <EditableCell productId={item.id} field="cost_price" value={item.cost_price} type="number" />
                  </td>
                  <td className="px-2 py-2 text-right text-green-400">
                    <EditableCell productId={item.id} field="selling_price" value={item.selling_price} type="number" />
                  </td>
                  <td className="px-2 py-2 text-right">{formatCurrency(item.stock)}</td>
                  <td className="px-2 py-2 text-right">
                    <EditableCell productId={item.id} field="min_stock" value={item.min_stock} type="number" />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        {filteredProducts.length > 100 && (
          <div className="p-4 text-center text-gray-400 border-t border-gray-700">
            Menampilkan 100 dari {filteredProducts.length} produk
          </div>
        )}
      </div>
    </div>
  );
};

export default MasterDatasheet;
