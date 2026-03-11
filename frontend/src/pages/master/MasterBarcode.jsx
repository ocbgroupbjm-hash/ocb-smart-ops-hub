import React, { useState, useEffect, useRef } from 'react';
import { QrCode, Printer, Search, Download, Upload, Barcode as BarcodeIcon } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';
import JsBarcode from 'jsbarcode';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MasterBarcode = () => {
  
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [printQty, setPrintQty] = useState(1);
  const [barcodeSize, setBarcodeSize] = useState('medium');
  const barcodeRefs = useRef({});

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/api/products?limit=500`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProducts(res.data.items || res.data || []);
    } catch (err) {
      console.error('Error fetching products:', err);
    } finally {
      setLoading(false);
    }
  };

  // Generate barcode using JsBarcode
  const generateBarcode = (productId, barcode) => {
    if (!barcode || !barcodeRefs.current[productId]) return;
    try {
      const sizeConfig = {
        small: { width: 1.5, height: 40, fontSize: 10 },
        medium: { width: 2, height: 60, fontSize: 12 },
        large: { width: 2.5, height: 80, fontSize: 14 }
      };
      const config = sizeConfig[barcodeSize];
      
      JsBarcode(barcodeRefs.current[productId], barcode, {
        format: 'CODE128',
        width: config.width,
        height: config.height,
        fontSize: config.fontSize,
        displayValue: true,
        background: '#ffffff',
        lineColor: '#000000'
      });
    } catch (err) {
      console.error('Error generating barcode:', err);
    }
  };

  useEffect(() => {
    // Generate barcodes for selected products
    selectedProducts.forEach(id => {
      const product = products.find(p => p.id === id);
      if (product?.barcode) {
        setTimeout(() => generateBarcode(id, product.barcode), 100);
      }
    });
  }, [selectedProducts, barcodeSize]);

  const toggleSelectProduct = (id) => {
    setSelectedProducts(prev => 
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    const allIds = filteredProducts.map(p => p.id);
    setSelectedProducts(allIds);
  };

  const clearSelection = () => {
    setSelectedProducts([]);
  };

  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      toast.error('Popup blocker aktif');
      return;
    }
    
    const selectedItems = products.filter(p => selectedProducts.includes(p.id));
    
    printWindow.document.write(`
      <html>
      <head>
        <title>Print Barcode</title>
        <style>
          body { font-family: Arial, sans-serif; }
          .barcode-grid { display: flex; flex-wrap: wrap; gap: 10px; padding: 20px; }
          .barcode-item { text-align: center; border: 1px dashed #ccc; padding: 10px; }
          .product-name { font-size: 10px; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
          .product-price { font-size: 12px; font-weight: bold; margin-top: 5px; }
          @media print { .barcode-item { break-inside: avoid; } }
        </style>
      </head>
      <body>
        <div class="barcode-grid">
    `);
    
    selectedItems.forEach(item => {
      for (let i = 0; i < printQty; i++) {
        printWindow.document.write(`
          <div class="barcode-item">
            <svg id="barcode-${item.id}-${i}"></svg>
            <div class="product-name">${item.name}</div>
            <div class="product-price">Rp ${(item.selling_price || 0).toLocaleString('id-ID')}</div>
          </div>
        `);
      }
    });
    
    printWindow.document.write(`
        </div>
        <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
        <script>
          window.onload = function() {
            ${selectedItems.map(item => 
              Array.from({ length: printQty }, (_, i) => 
                `try { JsBarcode("#barcode-${item.id}-${i}", "${item.barcode || item.code}", { format: "CODE128", width: 2, height: 60, fontSize: 12 }); } catch(e) {}`
              ).join('\n')
            ).join('\n')}
            setTimeout(() => { window.print(); window.close(); }, 500);
          };
        </script>
      </body>
      </html>
    `);
    printWindow.document.close();
  };

  const filteredProducts = products.filter(p =>
    p.name?.toLowerCase().includes(search.toLowerCase()) ||
    p.code?.toLowerCase().includes(search.toLowerCase()) ||
    p.barcode?.toLowerCase().includes(search.toLowerCase())
  );

  const formatCurrency = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  };

  return (
    <div className="p-6" data-testid="master-barcode">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BarcodeIcon className="w-6 h-6 text-yellow-500" />
          Manajemen Barcode
        </h1>
        <div className="flex gap-2">
          <Button variant="outline" className="border-gray-600" onClick={selectAll}>
            Pilih Semua
          </Button>
          <Button variant="outline" className="border-gray-600" onClick={clearSelection}>
            Batal Pilih
          </Button>
        </div>
      </div>

      {/* Print Controls */}
      <div className="bg-gray-800 rounded-lg p-4 mb-6 border border-gray-700">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">Ukuran:</span>
            <Select value={barcodeSize} onValueChange={setBarcodeSize}>
              <SelectTrigger className="w-32 bg-gray-900 border-gray-700">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="small">Kecil</SelectItem>
                <SelectItem value="medium">Sedang</SelectItem>
                <SelectItem value="large">Besar</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">Jumlah per item:</span>
            <Input
              type="number"
              min="1"
              max="100"
              value={printQty}
              onChange={(e) => setPrintQty(parseInt(e.target.value) || 1)}
              className="w-20 bg-gray-900 border-gray-700"
            />
          </div>
          <div className="flex-1" />
          <span className="text-gray-400 text-sm">{selectedProducts.length} item dipilih</span>
          <Button 
            onClick={handlePrint} 
            disabled={selectedProducts.length === 0}
            className="bg-yellow-600 hover:bg-yellow-700"
          >
            <Printer className="w-4 h-4 mr-2" /> Cetak Barcode
          </Button>
        </div>
      </div>

      {/* Search & Filter */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 mb-6">
        <div className="p-4">
          <div className="relative w-full max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Cari produk atau barcode..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-gray-900 border-gray-700"
            />
          </div>
        </div>
      </div>

      {/* Product List with Barcode Preview */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <table className="w-full">
          <thead className="bg-gray-900 text-gray-400 text-sm">
            <tr>
              <th className="px-4 py-3 text-center w-12">
                <input 
                  type="checkbox" 
                  checked={selectedProducts.length === filteredProducts.length && filteredProducts.length > 0}
                  onChange={() => selectedProducts.length === filteredProducts.length ? clearSelection() : selectAll()}
                  className="w-4 h-4"
                />
              </th>
              <th className="px-4 py-3 text-left">Kode</th>
              <th className="px-4 py-3 text-left">Barcode</th>
              <th className="px-4 py-3 text-left">Nama Produk</th>
              <th className="px-4 py-3 text-right">Harga Jual</th>
              <th className="px-4 py-3 text-center">Preview</th>
            </tr>
          </thead>
          <tbody className="text-white">
            {loading ? (
              <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">Memuat data...</td></tr>
            ) : filteredProducts.length === 0 ? (
              <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">Tidak ada produk ditemukan</td></tr>
            ) : (
              filteredProducts.slice(0, 50).map((item) => (
                <tr 
                  key={item.id} 
                  className={`border-t border-gray-700 hover:bg-gray-700/50 cursor-pointer ${selectedProducts.includes(item.id) ? 'bg-yellow-900/20' : ''}`}
                  onClick={() => toggleSelectProduct(item.id)}
                >
                  <td className="px-4 py-3 text-center">
                    <input 
                      type="checkbox" 
                      checked={selectedProducts.includes(item.id)}
                      onChange={() => toggleSelectProduct(item.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-4 h-4"
                    />
                  </td>
                  <td className="px-4 py-3 font-mono text-yellow-400">{item.code}</td>
                  <td className="px-4 py-3 font-mono text-gray-400">{item.barcode || item.code}</td>
                  <td className="px-4 py-3">{item.name}</td>
                  <td className="px-4 py-3 text-right text-green-400">{formatCurrency(item.selling_price)}</td>
                  <td className="px-4 py-3 text-center bg-white">
                    {selectedProducts.includes(item.id) && (
                      <svg ref={el => barcodeRefs.current[item.id] = el} />
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        {filteredProducts.length > 50 && (
          <div className="p-4 text-center text-gray-400 border-t border-gray-700">
            Menampilkan 50 dari {filteredProducts.length} produk. Gunakan filter untuk mempersempit pencarian.
          </div>
        )}
      </div>
    </div>
  );
};

export default MasterBarcode;
