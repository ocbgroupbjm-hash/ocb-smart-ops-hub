import React, { useState, useEffect, useCallback } from 'react';
import { Table, Search, Download, Edit2, Save, X, CheckSquare, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ============================================================
// DATA SHEET MODULE - GLOBAL ITEM EDITOR
// ============================================================
// FUNGSI: Edit massal, bulk update, export, search, filter
// TIDAK BOLEH: Create new item, delete item, create transaction
// Pembuatan item hanya melalui: Master Data → Items
// ============================================================

const MasterDatasheet = () => {
  // Data type selector
  const [dataType, setDataType] = useState('products');
  
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [editingCell, setEditingCell] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [selectedRows, setSelectedRows] = useState([]);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [brandFilter, setBrandFilter] = useState('');
  
  // Bulk edit state
  const [bulkEditMode, setBulkEditMode] = useState(false);
  const [bulkEditField, setBulkEditField] = useState('');
  const [bulkEditValue, setBulkEditValue] = useState('');

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem('token');
    return { headers: { Authorization: `Bearer ${token}` } };
  }, []);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders().headers;
      
      // ============================================================
      // CORRECT ENDPOINTS FOR SSOT MASTER DATA
      // Customers: /api/customers → {items: [], total: X}
      // Suppliers: /api/suppliers → {items: [], total: X}
      // Employees: /api/erp/employees → {employees: [], total: X}
      // ============================================================
      
      const [productsRes, customersRes, suppliersRes, employeesRes, categoriesRes, brandsRes, unitsRes] = await Promise.all([
        axios.get(`${API_URL}/api/products?limit=500`, { headers }).catch(e => ({ data: { items: [] } })),
        axios.get(`${API_URL}/api/customers`, { headers }).catch(e => ({ data: { items: [] } })),
        axios.get(`${API_URL}/api/suppliers`, { headers }).catch(e => ({ data: { items: [] } })),
        axios.get(`${API_URL}/api/erp/employees`, { headers }).catch(e => ({ data: { employees: [] } })),
        axios.get(`${API_URL}/api/categories`, { headers }).catch(e => ({ data: { items: [] } })),
        axios.get(`${API_URL}/api/brands`, { headers }).catch(e => ({ data: { items: [] } })),
        axios.get(`${API_URL}/api/units`, { headers }).catch(e => ({ data: { items: [] } }))
      ]);
      
      // Parse responses with correct field names
      setProducts(productsRes.data.items || productsRes.data || []);
      setCustomers(customersRes.data.items || customersRes.data.customers || customersRes.data || []);
      setSuppliers(suppliersRes.data.items || suppliersRes.data.suppliers || suppliersRes.data || []);
      setEmployees(employeesRes.data.employees || employeesRes.data.items || employeesRes.data || []);
      setCategories(categoriesRes.data.items || categoriesRes.data.categories || categoriesRes.data || []);
      setBrands(brandsRes.data.items || brandsRes.data.brands || brandsRes.data || []);
      setUnits(unitsRes.data.items || unitsRes.data.units || unitsRes.data || []);
      
      toast.success('Data berhasil dimuat');
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Gagal memuat data. Silakan refresh halaman.');
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // Get current data based on type
  const getCurrentData = () => {
    switch (dataType) {
      case 'products': return products;
      case 'customers': return customers;
      case 'suppliers': return suppliers;
      case 'employees': return employees;
      default: return products;
    }
  };

  const handleCellClick = (itemId, field, value) => {
    setEditingCell({ itemId, field });
    setEditValue(value || '');
  };

  const handleSaveCellWithId = async (itemId, field, newValue) => {
    try {
      let endpoint = '';
      let updateData = {};
      
      // ============================================================
      // CORRECT UPDATE ENDPOINTS FOR SSOT MASTER DATA
      // ============================================================
      switch (dataType) {
        case 'products':
          endpoint = `/api/products/${itemId}`;
          break;
        case 'customers':
          endpoint = `/api/customers/${itemId}`;
          break;
        case 'suppliers':
          endpoint = `/api/suppliers/${itemId}`;
          break;
        case 'employees':
          endpoint = `/api/erp/employees/${itemId}`;
          break;
        default:
          endpoint = `/api/products/${itemId}`;
      }
      
      // Parse numeric fields
      if (['cost_price', 'selling_price', 'min_stock', 'credit_limit', 'basic_salary'].includes(field)) {
        updateData[field] = parseFloat(newValue) || 0;
      } else {
        updateData[field] = newValue;
      }
      
      await axios.put(`${API_URL}${endpoint}`, updateData, getAuthHeaders());
      
      // Update local state
      const updateLocalState = (setter, data) => {
        setter(data.map(item => 
          item.id === itemId ? { ...item, ...updateData } : item
        ));
      };
      
      switch (dataType) {
        case 'products':
          updateLocalState(setProducts, products);
          break;
        case 'customers':
          updateLocalState(setCustomers, customers);
          break;
        case 'suppliers':
          updateLocalState(setSuppliers, suppliers);
          break;
        case 'employees':
          updateLocalState(setEmployees, employees);
          break;
      }
      
      toast.success('Data berhasil diupdate');
      setEditingCell(null);
      
      // Log activity for audit
      await axios.post(`${API_URL}/api/activity-log`, {
        action: 'datasheet_edit',
        entity_type: dataType,
        entity_id: itemId,
        changes: { field, old_value: 'N/A', new_value: newValue }
      }, getAuthHeaders()).catch(() => {});
      
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal update');
    }
  };

  const handleSaveCell = async () => {
    if (!editingCell) return;
    await handleSaveCellWithId(editingCell.itemId, editingCell.field, editValue);
  };

  const handleCancelEdit = () => {
    setEditingCell(null);
    setEditValue('');
  };

  // Bulk Update
  const handleBulkUpdate = async () => {
    if (selectedRows.length === 0) {
      toast.warning('Pilih minimal 1 item untuk bulk update');
      return;
    }
    if (!bulkEditField || bulkEditValue === '') {
      toast.warning('Pilih field dan masukkan nilai baru');
      return;
    }
    
    setLoading(true);
    try {
      let successCount = 0;
      for (const itemId of selectedRows) {
        try {
          await handleSaveCellWithId(itemId, bulkEditField, bulkEditValue);
          successCount++;
        } catch (err) {
          console.error(`Failed to update ${itemId}:`, err);
        }
      }
      
      toast.success(`${successCount} dari ${selectedRows.length} item berhasil diupdate`);
      setBulkEditMode(false);
      setBulkEditField('');
      setBulkEditValue('');
      setSelectedRows([]);
      await fetchAll();
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    const data = getCurrentData();
    let headers = [];
    let rows = [];
    
    switch (dataType) {
      case 'products':
        headers = ['Kode', 'Barcode', 'Nama', 'Kategori', 'Merk', 'Satuan', 'Harga Beli', 'Harga Jual', 'Stok', 'Min Stok'];
        rows = data.map(p => [p.code, p.barcode || '', p.name, p.category_name || '', p.brand_name || '', p.unit_name || '', p.cost_price || 0, p.selling_price || 0, p.stock || 0, p.min_stock || 0]);
        break;
      case 'customers':
        headers = ['Kode', 'Nama', 'Telepon', 'Email', 'Alamat', 'Credit Limit'];
        rows = data.map(c => [c.code || '', c.name, c.phone || '', c.email || '', c.address || '', c.credit_limit || 0]);
        break;
      case 'suppliers':
        headers = ['Kode', 'Nama', 'Telepon', 'Email', 'Alamat', 'Contact Person'];
        rows = data.map(s => [s.code || '', s.name, s.phone || '', s.email || '', s.address || '', s.contact_person || '']);
        break;
      case 'employees':
        headers = ['NIK', 'Nama', 'Email', 'Telepon', 'Jabatan', 'Department'];
        rows = data.map(e => [e.nik || '', e.name, e.email || '', e.phone || '', e.position || '', e.department || '']);
        break;
    }
    
    const csvContent = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `datasheet-${dataType}.csv`;
    a.click();
    toast.success('Data berhasil diexport');
  };

  const toggleRowSelect = (id) => {
    setSelectedRows(prev => 
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    const data = getFilteredData();
    if (selectedRows.length === data.length) {
      setSelectedRows([]);
    } else {
      setSelectedRows(data.map(item => item.id));
    }
  };

  const getFilteredData = () => {
    const data = getCurrentData();
    return data.filter(item => {
      const matchesSearch = !search || 
        item.name?.toLowerCase().includes(search.toLowerCase()) ||
        item.code?.toLowerCase().includes(search.toLowerCase()) ||
        item.nik?.toLowerCase().includes(search.toLowerCase());
      const matchesCategory = !categoryFilter || item.category_id === categoryFilter;
      const matchesBrand = !brandFilter || item.brand_id === brandFilter;
      return matchesSearch && (dataType !== 'products' || (matchesCategory && matchesBrand));
    });
  };

  const filteredData = getFilteredData();

  const formatCurrency = (num) => new Intl.NumberFormat('id-ID').format(num || 0);

  const EditableCell = ({ itemId, field, value, type = 'text' }) => {
    const isEditing = editingCell?.itemId === itemId && editingCell?.field === field;
    
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
        onClick={() => handleCellClick(itemId, field, value)}
        data-testid={`cell-${field}-${itemId}`}
      >
        {type === 'number' ? formatCurrency(value) : (value || '-')}
      </span>
    );
  };

  const EditableSelectCell = ({ itemId, field, currentValue, currentName, options }) => {
    const isEditing = editingCell?.itemId === itemId && editingCell?.field === field;
    
    if (isEditing) {
      return (
        <div className="flex items-center gap-1">
          <Select 
            value={editValue || 'none'} 
            onValueChange={async (val) => {
              setEditValue(val === 'none' ? '' : val);
              await handleSaveCellWithId(itemId, field, val === 'none' ? '' : val);
            }}
          >
            <SelectTrigger className="h-7 text-xs bg-gray-900 border-gray-600 w-full">
              <SelectValue placeholder="Pilih..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">-- Tidak ada --</SelectItem>
              {options.map(opt => (
                <SelectItem key={opt.id} value={opt.id}>{opt.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button size="sm" variant="ghost" onClick={handleCancelEdit} className="h-6 w-6 p-0">
            <X className="w-3 h-3 text-red-400" />
          </Button>
        </div>
      );
    }
    
    return (
      <span 
        className="cursor-pointer hover:bg-gray-700 px-2 py-1 rounded block text-gray-400 hover:text-white"
        onClick={() => handleCellClick(itemId, field, currentValue)}
      >
        {currentName || '-'}
      </span>
    );
  };

  // Get bulk edit fields based on data type
  const getBulkEditFields = () => {
    switch (dataType) {
      case 'products':
        return [
          { value: 'category_id', label: 'Kategori' },
          { value: 'brand_id', label: 'Merk' },
          { value: 'cost_price', label: 'Harga Beli' },
          { value: 'selling_price', label: 'Harga Jual' },
          { value: 'min_stock', label: 'Min Stok' }
        ];
      case 'customers':
        return [
          { value: 'credit_limit', label: 'Credit Limit' },
          { value: 'payment_term', label: 'Payment Term' }
        ];
      case 'suppliers':
        return [
          { value: 'payment_term', label: 'Payment Term' }
        ];
      case 'employees':
        return [
          { value: 'department', label: 'Department' },
          { value: 'position', label: 'Jabatan' }
        ];
      default:
        return [];
    }
  };

  return (
    <div className="p-6" data-testid="master-datasheet">
      {/* Error State */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-2 text-red-300">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
            <Button size="sm" variant="outline" className="ml-4 border-red-600" onClick={fetchAll}>
              Coba Lagi
            </Button>
          </div>
        </div>
      )}
      
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Table className="w-6 h-6 text-yellow-500" />
          Data Sheet
          <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-green-600 text-white rounded">NEW</span>
        </h1>
        <div className="flex gap-2">
          <Button onClick={fetchAll} variant="outline" className="border-gray-600" disabled={loading} data-testid="btn-refresh">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </Button>
          <Button onClick={handleExport} variant="outline" className="border-gray-600" data-testid="btn-export">
            <Download className="w-4 h-4 mr-2" /> Export CSV
          </Button>
        </div>
      </div>

      {/* Info Banner - Data Sheet Purpose */}
      <div className="bg-amber-900/30 border border-amber-700 rounded-lg p-3 mb-4">
        <p className="text-amber-300 text-sm">
          <strong>Data Sheet</strong> adalah modul untuk <strong>edit massal</strong> item existing. 
          Untuk membuat item baru, gunakan menu <strong>Master Data → Items</strong>.
        </p>
      </div>

      {/* Data Type Selector */}
      <div className="bg-gray-800 rounded-lg p-4 mb-4 border border-gray-700">
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">Tipe Data:</span>
          <div className="flex gap-2">
            {[
              { value: 'products', label: 'Produk' },
              { value: 'customers', label: 'Pelanggan' },
              { value: 'suppliers', label: 'Supplier' },
              { value: 'employees', label: 'Karyawan' }
            ].map(type => (
              <Button
                key={type.value}
                variant={dataType === type.value ? "default" : "outline"}
                size="sm"
                onClick={() => { setDataType(type.value); setSelectedRows([]); }}
                className={dataType === type.value ? "bg-yellow-600 hover:bg-yellow-700" : "border-gray-600"}
              >
                {type.label}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-gray-800 rounded-lg p-4 mb-4 border border-gray-700">
        <div className="flex gap-4 items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Cari..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-gray-900 border-gray-700"
            />
          </div>
          {dataType === 'products' && (
            <>
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
            </>
          )}
          <span className="text-gray-400 text-sm">{filteredData.length} item</span>
        </div>
      </div>

      {/* Bulk Actions - EDIT ONLY (No Delete in Data Sheet) */}
      {selectedRows.length > 0 && (
        <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <CheckSquare className="w-5 h-5 text-yellow-400" />
              <span className="text-yellow-300">{selectedRows.length} item dipilih</span>
              
              {!bulkEditMode ? (
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" className="border-yellow-600 text-yellow-400" onClick={() => setBulkEditMode(true)} data-testid="btn-bulk-edit">
                    <Edit2 className="w-4 h-4 mr-2" /> Bulk Edit
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Select value={bulkEditField} onValueChange={setBulkEditField}>
                    <SelectTrigger className="w-40 bg-gray-900 border-gray-600">
                      <SelectValue placeholder="Pilih Field" />
                    </SelectTrigger>
                    <SelectContent>
                      {getBulkEditFields().map(f => (
                        <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input
                    placeholder="Nilai baru..."
                    value={bulkEditValue}
                    onChange={(e) => setBulkEditValue(e.target.value)}
                    className="w-40 bg-gray-900 border-gray-600"
                    data-testid="bulk-edit-value"
                  />
                  <Button size="sm" className="bg-green-600" onClick={handleBulkUpdate} disabled={loading} data-testid="btn-apply-bulk">
                    <Save className="w-4 h-4 mr-2" /> Apply
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => { setBulkEditMode(false); setBulkEditField(''); setBulkEditValue(''); }}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              )}
            </div>
            <Button size="sm" variant="ghost" onClick={() => setSelectedRows([])}>
              Batal Pilih
            </Button>
          </div>
        </div>
      )}

      {/* Usage Tips */}
      <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-3 mb-4">
        <p className="text-blue-300 text-sm">
          <strong>Tips:</strong> Klik pada sel untuk edit langsung. 
          <span className="text-green-300 ml-2">• Tekan Enter untuk simpan, Escape untuk batal.</span>
          <span className="text-yellow-300 ml-2">• Pilih checkbox untuk bulk edit.</span>
        </p>
      </div>

      {/* Datasheet Table */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-x-auto">
        {dataType === 'products' ? (
          <table className="w-full min-w-[1200px]">
            <thead className="bg-gray-900 text-gray-400 text-xs sticky top-0">
              <tr>
                <th className="px-2 py-3 text-center w-10">
                  <input type="checkbox" className="w-4 h-4" checked={selectedRows.length === filteredData.length && filteredData.length > 0} onChange={toggleSelectAll} />
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
              ) : filteredData.length === 0 ? (
                <tr><td colSpan="11" className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : (
                filteredData.slice(0, 100).map((item) => (
                  <tr key={item.id} className={`border-t border-gray-700 hover:bg-gray-700/50 ${selectedRows.includes(item.id) ? 'bg-yellow-900/20' : ''}`}>
                    <td className="px-2 py-2 text-center">
                      <input type="checkbox" checked={selectedRows.includes(item.id)} onChange={() => toggleRowSelect(item.id)} className="w-4 h-4" />
                    </td>
                    <td className="px-2 py-2 font-mono text-yellow-400 text-xs">{item.code}</td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="barcode" value={item.barcode} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="name" value={item.name} /></td>
                    <td className="px-2 py-2"><EditableSelectCell itemId={item.id} field="category_id" currentValue={item.category_id} currentName={item.category_name} options={categories} /></td>
                    <td className="px-2 py-2"><EditableSelectCell itemId={item.id} field="brand_id" currentValue={item.brand_id} currentName={item.brand_name} options={brands} /></td>
                    <td className="px-2 py-2"><EditableSelectCell itemId={item.id} field="unit_id" currentValue={item.unit_id} currentName={item.unit_name} options={units} /></td>
                    <td className="px-2 py-2 text-right"><EditableCell itemId={item.id} field="cost_price" value={item.cost_price} type="number" /></td>
                    <td className="px-2 py-2 text-right text-green-400"><EditableCell itemId={item.id} field="selling_price" value={item.selling_price} type="number" /></td>
                    <td className="px-2 py-2 text-right">{formatCurrency(item.stock)}</td>
                    <td className="px-2 py-2 text-right"><EditableCell itemId={item.id} field="min_stock" value={item.min_stock} type="number" /></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        ) : dataType === 'customers' ? (
          <table className="w-full min-w-[800px]">
            <thead className="bg-gray-900 text-gray-400 text-xs sticky top-0">
              <tr>
                <th className="px-2 py-3 text-center w-10"><input type="checkbox" className="w-4 h-4" checked={selectedRows.length === filteredData.length && filteredData.length > 0} onChange={toggleSelectAll} /></th>
                <th className="px-2 py-3 text-left">Kode</th>
                <th className="px-2 py-3 text-left">Nama</th>
                <th className="px-2 py-3 text-left">Telepon</th>
                <th className="px-2 py-3 text-left">Email</th>
                <th className="px-2 py-3 text-left">Alamat</th>
                <th className="px-2 py-3 text-right">Credit Limit</th>
              </tr>
            </thead>
            <tbody className="text-white text-sm">
              {loading ? (
                <tr><td colSpan="7" className="px-4 py-8 text-center text-gray-400">Memuat data...</td></tr>
              ) : filteredData.length === 0 ? (
                <tr><td colSpan="7" className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : (
                filteredData.slice(0, 100).map((item) => (
                  <tr key={item.id} className={`border-t border-gray-700 hover:bg-gray-700/50 ${selectedRows.includes(item.id) ? 'bg-yellow-900/20' : ''}`}>
                    <td className="px-2 py-2 text-center"><input type="checkbox" checked={selectedRows.includes(item.id)} onChange={() => toggleRowSelect(item.id)} className="w-4 h-4" /></td>
                    <td className="px-2 py-2 font-mono text-yellow-400 text-xs">{item.code}</td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="name" value={item.name} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="phone" value={item.phone} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="email" value={item.email} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="address" value={item.address} /></td>
                    <td className="px-2 py-2 text-right"><EditableCell itemId={item.id} field="credit_limit" value={item.credit_limit} type="number" /></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        ) : dataType === 'suppliers' ? (
          <table className="w-full min-w-[800px]">
            <thead className="bg-gray-900 text-gray-400 text-xs sticky top-0">
              <tr>
                <th className="px-2 py-3 text-center w-10"><input type="checkbox" className="w-4 h-4" checked={selectedRows.length === filteredData.length && filteredData.length > 0} onChange={toggleSelectAll} /></th>
                <th className="px-2 py-3 text-left">Kode</th>
                <th className="px-2 py-3 text-left">Nama</th>
                <th className="px-2 py-3 text-left">Contact Person</th>
                <th className="px-2 py-3 text-left">Telepon</th>
                <th className="px-2 py-3 text-left">Email</th>
                <th className="px-2 py-3 text-left">Alamat</th>
              </tr>
            </thead>
            <tbody className="text-white text-sm">
              {loading ? (
                <tr><td colSpan="7" className="px-4 py-8 text-center text-gray-400">Memuat data...</td></tr>
              ) : filteredData.length === 0 ? (
                <tr><td colSpan="7" className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : (
                filteredData.slice(0, 100).map((item) => (
                  <tr key={item.id} className={`border-t border-gray-700 hover:bg-gray-700/50 ${selectedRows.includes(item.id) ? 'bg-yellow-900/20' : ''}`}>
                    <td className="px-2 py-2 text-center"><input type="checkbox" checked={selectedRows.includes(item.id)} onChange={() => toggleRowSelect(item.id)} className="w-4 h-4" /></td>
                    <td className="px-2 py-2 font-mono text-yellow-400 text-xs">{item.code}</td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="name" value={item.name} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="contact_person" value={item.contact_person} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="phone" value={item.phone} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="email" value={item.email} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="address" value={item.address} /></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        ) : (
          <table className="w-full min-w-[800px]">
            <thead className="bg-gray-900 text-gray-400 text-xs sticky top-0">
              <tr>
                <th className="px-2 py-3 text-center w-10"><input type="checkbox" className="w-4 h-4" checked={selectedRows.length === filteredData.length && filteredData.length > 0} onChange={toggleSelectAll} /></th>
                <th className="px-2 py-3 text-left">NIK</th>
                <th className="px-2 py-3 text-left">Nama</th>
                <th className="px-2 py-3 text-left">Email</th>
                <th className="px-2 py-3 text-left">Telepon</th>
                <th className="px-2 py-3 text-left">Jabatan</th>
                <th className="px-2 py-3 text-left">Department</th>
              </tr>
            </thead>
            <tbody className="text-white text-sm">
              {loading ? (
                <tr><td colSpan="7" className="px-4 py-8 text-center text-gray-400">Memuat data...</td></tr>
              ) : filteredData.length === 0 ? (
                <tr><td colSpan="7" className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
              ) : (
                filteredData.slice(0, 100).map((item) => (
                  <tr key={item.id} className={`border-t border-gray-700 hover:bg-gray-700/50 ${selectedRows.includes(item.id) ? 'bg-yellow-900/20' : ''}`}>
                    <td className="px-2 py-2 text-center"><input type="checkbox" checked={selectedRows.includes(item.id)} onChange={() => toggleRowSelect(item.id)} className="w-4 h-4" /></td>
                    <td className="px-2 py-2 font-mono text-yellow-400 text-xs">{item.nik}</td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="name" value={item.name} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="email" value={item.email} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="phone" value={item.phone} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="position" value={item.position} /></td>
                    <td className="px-2 py-2"><EditableCell itemId={item.id} field="department" value={item.department} /></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
        {filteredData.length > 100 && (
          <div className="p-4 text-center text-gray-400 border-t border-gray-700">
            Menampilkan 100 dari {filteredData.length} item
          </div>
        )}
      </div>
    </div>
  );
};

export default MasterDatasheet;
