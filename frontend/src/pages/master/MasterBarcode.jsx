import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  QrCode, Printer, Search, Plus, Edit2, Trash2, X, Save, Eye,
  Barcode as BarcodeIcon, Settings, Grid, List, Tag, DollarSign
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import JsBarcode from 'jsbarcode';

const MasterBarcode = () => {
  const { api } = useAuth();
  
  // State
  const [products, setProducts] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]); // with qty
  
  // Print Settings
  const [printMode, setPrintMode] = useState('selected'); // single, all, selected, rack
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [barcodeSource, setBarcodeSource] = useState('barcode'); // barcode, item_code, sku
  const [priceDisplay, setPriceDisplay] = useState('price_sell'); // price_buy, price_sell, both, none
  const [showPreview, setShowPreview] = useState(false);
  
  // Template Modal
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [templateForm, setTemplateForm] = useState({
    template_name: '',
    width: 58,
    height: 40,
    margin: 2,
    gap: 2,
    barcode_type: 'CODE128',
    font_size: 10,
    show_price: true,
    show_name: true
  });

  const previewRefs = useRef({});

  // Default Templates
  const defaultTemplates = [
    { id: 'default-1', template_name: 'Label 58x40', width: 58, height: 40, margin: 2, gap: 2, barcode_type: 'CODE128', font_size: 10, show_price: true, show_name: true },
    { id: 'default-2', template_name: 'Label 38x25', width: 38, height: 25, margin: 1, gap: 1, barcode_type: 'CODE128', font_size: 8, show_price: true, show_name: true },
    { id: 'default-3', template_name: 'A4 30 Label', width: 63, height: 30, margin: 2, gap: 0, barcode_type: 'CODE128', font_size: 9, show_price: true, show_name: true },
    { id: 'default-4', template_name: 'Rak / Shelf', width: 80, height: 50, margin: 3, gap: 3, barcode_type: 'CODE128', font_size: 12, show_price: true, show_name: true },
  ];

  // Load products
  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/products?limit=500&search=${search}`);
      if (res.ok) {
        const data = await res.json();
        setProducts(data.items || data || []);
      }
    } catch (err) {
      console.error('Error loading products:', err);
    } finally {
      setLoading(false);
    }
  }, [api, search]);

  // Load templates
  const loadTemplates = useCallback(async () => {
    try {
      const res = await api('/api/barcode/templates');
      if (res.ok) {
        const data = await res.json();
        setTemplates(data.length > 0 ? data : defaultTemplates);
        if (data.length > 0 || defaultTemplates.length > 0) {
          setSelectedTemplate(data[0]?.id || defaultTemplates[0].id);
        }
      } else {
        setTemplates(defaultTemplates);
        setSelectedTemplate(defaultTemplates[0].id);
      }
    } catch {
      setTemplates(defaultTemplates);
      setSelectedTemplate(defaultTemplates[0].id);
    }
  }, [api]);

  useEffect(() => {
    loadProducts();
    loadTemplates();
  }, [loadProducts, loadTemplates]);

  // Generate barcode preview
  useEffect(() => {
    selectedItems.forEach(item => {
      if (previewRefs.current[item.id]) {
        const barcodeValue = getBarcodeValue(item);
        if (barcodeValue) {
          try {
            const template = templates.find(t => t.id === selectedTemplate) || defaultTemplates[0];
            JsBarcode(previewRefs.current[item.id], barcodeValue, {
              format: template.barcode_type || 'CODE128',
              width: 1.5,
              height: 40,
              fontSize: template.font_size || 10,
              displayValue: true,
              background: '#ffffff',
              lineColor: '#000000'
            });
          } catch (err) {
            console.error('Error generating barcode:', err);
          }
        }
      }
    });
  }, [selectedItems, selectedTemplate, barcodeSource, templates]);

  const getBarcodeValue = (product) => {
    switch (barcodeSource) {
      case 'item_code': return product.code || '';
      case 'sku': return product.sku || product.code || '';
      default: return product.barcode || product.code || '';
    }
  };

  const getPrice = (product, type) => {
    switch (type) {
      case 'price_buy': return product.cost_price || 0;
      case 'price_sell': return product.selling_price || 0;
      case 'both': return { buy: product.cost_price || 0, sell: product.selling_price || 0 };
      default: return null;
    }
  };

  const formatCurrency = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  };

  // Toggle product selection
  const toggleSelectProduct = (product) => {
    const exists = selectedItems.find(i => i.id === product.id);
    if (exists) {
      setSelectedItems(prev => prev.filter(i => i.id !== product.id));
    } else {
      setSelectedItems(prev => [...prev, { ...product, print_qty: 1 }]);
    }
  };

  // Update quantity for selected item
  const updateItemQty = (id, qty) => {
    setSelectedItems(prev => prev.map(item => 
      item.id === id ? { ...item, print_qty: Math.max(1, qty) } : item
    ));
  };

  // Select all products
  const selectAll = () => {
    const filteredProds = filteredProducts.slice(0, 100);
    setSelectedItems(filteredProds.map(p => ({ ...p, print_qty: 1 })));
  };

  // Clear selection
  const clearSelection = () => {
    setSelectedItems([]);
  };

  // Save template
  const saveTemplate = async () => {
    try {
      const payload = { ...templateForm };
      const url = editingTemplate 
        ? `/api/barcode/templates/${editingTemplate.id}` 
        : '/api/barcode/templates';
      const method = editingTemplate ? 'PUT' : 'POST';
      
      const res = await api(url, { method, body: JSON.stringify(payload) });
      if (res.ok) {
        toast.success(editingTemplate ? 'Template diupdate' : 'Template ditambahkan');
        loadTemplates();
        setShowTemplateModal(false);
        resetTemplateForm();
      }
    } catch (err) {
      toast.error('Gagal menyimpan template');
    }
  };

  const deleteTemplate = async (id) => {
    if (!confirm('Hapus template ini?')) return;
    try {
      const res = await api(`/api/barcode/templates/${id}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Template dihapus');
        loadTemplates();
      }
    } catch {
      toast.error('Gagal menghapus template');
    }
  };

  const resetTemplateForm = () => {
    setEditingTemplate(null);
    setTemplateForm({
      template_name: '',
      width: 58,
      height: 40,
      margin: 2,
      gap: 2,
      barcode_type: 'CODE128',
      font_size: 10,
      show_price: true,
      show_name: true
    });
  };

  const editTemplate = (template) => {
    setEditingTemplate(template);
    setTemplateForm({
      template_name: template.template_name,
      width: template.width,
      height: template.height,
      margin: template.margin,
      gap: template.gap,
      barcode_type: template.barcode_type,
      font_size: template.font_size,
      show_price: template.show_price,
      show_name: template.show_name
    });
    setShowTemplateModal(true);
  };

  // Print barcode
  const handlePrint = () => {
    if (selectedItems.length === 0) {
      toast.error('Pilih minimal 1 item');
      return;
    }

    const template = templates.find(t => t.id === selectedTemplate) || defaultTemplates[0];
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      toast.error('Popup blocker aktif. Izinkan popup untuk cetak.');
      return;
    }

    const labelWidth = template.width;
    const labelHeight = template.height;
    const margin = template.margin;
    const gap = template.gap;

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Print Barcode - ${template.template_name}</title>
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body { font-family: Arial, sans-serif; background: #fff; }
          .barcode-container { 
            display: flex; flex-wrap: wrap; 
            gap: ${gap}mm; padding: ${margin}mm;
          }
          .barcode-label {
            width: ${labelWidth}mm;
            height: ${labelHeight}mm;
            border: 1px dashed #ccc;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2mm;
            page-break-inside: avoid;
            overflow: hidden;
          }
          .barcode-label svg { max-width: 100%; height: auto; }
          .product-name { 
            font-size: ${Math.max(template.font_size - 2, 7)}px; 
            text-align: center;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-top: 1mm;
          }
          .product-price { 
            font-size: ${template.font_size}px; 
            font-weight: bold; 
            margin-top: 1mm;
          }
          .price-buy { color: #666; font-size: ${template.font_size - 1}px; }
          @media print { 
            .barcode-label { border: none; }
            body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          }
        </style>
      </head>
      <body>
        <div class="barcode-container">
    `);

    selectedItems.forEach(item => {
      const barcodeValue = getBarcodeValue(item);
      const qty = item.print_qty || 1;
      
      for (let i = 0; i < qty; i++) {
        let priceHtml = '';
        if (priceDisplay !== 'none' && template.show_price) {
          if (priceDisplay === 'both') {
            priceHtml = `
              <div class="price-buy">Beli: ${formatCurrency(item.cost_price)}</div>
              <div class="product-price">Jual: ${formatCurrency(item.selling_price)}</div>
            `;
          } else if (priceDisplay === 'price_buy') {
            priceHtml = `<div class="product-price">${formatCurrency(item.cost_price)}</div>`;
          } else {
            priceHtml = `<div class="product-price">${formatCurrency(item.selling_price)}</div>`;
          }
        }

        printWindow.document.write(`
          <div class="barcode-label">
            <svg id="bc-${item.id}-${i}"></svg>
            ${template.show_name ? `<div class="product-name">${item.name}</div>` : ''}
            ${priceHtml}
          </div>
        `);
      }
    });

    printWindow.document.write(`
        </div>
        <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"><\/script>
        <script>
          window.onload = function() {
            ${selectedItems.map(item => {
              const barcodeValue = getBarcodeValue(item);
              const qty = item.print_qty || 1;
              return Array.from({ length: qty }, (_, i) => 
                `try { JsBarcode("#bc-${item.id}-${i}", "${barcodeValue}", { 
                  format: "${template.barcode_type || 'CODE128'}", 
                  width: 1.5, 
                  height: ${Math.min(labelHeight * 0.4, 50)}, 
                  fontSize: ${template.font_size},
                  displayValue: true,
                  margin: 0
                }); } catch(e) { console.error(e); }`
              ).join('\n');
            }).join('\n')}
            setTimeout(() => { window.print(); }, 500);
          };
        <\/script>
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

  const currentTemplate = templates.find(t => t.id === selectedTemplate) || defaultTemplates[0];

  return (
    <div className="space-y-4" data-testid="master-barcode">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
            <BarcodeIcon className="h-6 w-6 text-amber-400" />
            Cetak Barcode
          </h1>
          <p className="text-gray-400 text-sm">Cetak label barcode dengan berbagai template</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            className="border-red-900/30 text-gray-300"
            onClick={() => { resetTemplateForm(); setShowTemplateModal(true); }}
          >
            <Plus className="h-4 w-4 mr-1" /> Template Baru
          </Button>
        </div>
      </div>

      {/* Main Layout - 2 Columns */}
      <div className="grid grid-cols-12 gap-4">
        {/* Left Panel - Templates */}
        <div className="col-span-3 bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <h3 className="text-amber-200 font-semibold mb-3 flex items-center gap-2">
            <Grid className="h-4 w-4" /> Template Label
          </h3>
          <div className="space-y-2">
            {templates.map(template => (
              <div 
                key={template.id}
                onClick={() => setSelectedTemplate(template.id)}
                className={`p-3 rounded-lg cursor-pointer transition-all ${
                  selectedTemplate === template.id 
                    ? 'bg-amber-600/20 border border-amber-600/50' 
                    : 'bg-[#0a0608] border border-red-900/20 hover:border-red-900/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-200">{template.template_name}</span>
                  {!template.id.startsWith('default-') && (
                    <div className="flex gap-1">
                      <button onClick={(e) => { e.stopPropagation(); editTemplate(template); }} className="p-1 hover:bg-blue-600/20 rounded">
                        <Edit2 className="h-3 w-3 text-blue-400" />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); deleteTemplate(template.id); }} className="p-1 hover:bg-red-600/20 rounded">
                        <Trash2 className="h-3 w-3 text-red-400" />
                      </button>
                    </div>
                  )}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {template.width}x{template.height}mm
                </div>
              </div>
            ))}
          </div>

          {/* Print Settings */}
          <div className="mt-4 pt-4 border-t border-red-900/30">
            <h4 className="text-amber-200 text-sm font-semibold mb-3 flex items-center gap-2">
              <Settings className="h-4 w-4" /> Pengaturan Print
            </h4>
            
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Mode Print</label>
                <Select value={printMode} onValueChange={setPrintMode}>
                  <SelectTrigger className="w-full bg-[#0a0608] border-red-900/30 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="selected">Item Terpilih</SelectItem>
                    <SelectItem value="all">Semua Item</SelectItem>
                    <SelectItem value="rack">Label Rak</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs text-gray-400 mb-1 block">Sumber Barcode</label>
                <Select value={barcodeSource} onValueChange={setBarcodeSource}>
                  <SelectTrigger className="w-full bg-[#0a0608] border-red-900/30 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="barcode">Barcode</SelectItem>
                    <SelectItem value="item_code">Kode Item</SelectItem>
                    <SelectItem value="sku">SKU</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs text-gray-400 mb-1 block">Tampilan Harga</label>
                <Select value={priceDisplay} onValueChange={setPriceDisplay}>
                  <SelectTrigger className="w-full bg-[#0a0608] border-red-900/30 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="price_sell">Harga Jual</SelectItem>
                    <SelectItem value="price_buy">Harga Beli</SelectItem>
                    <SelectItem value="both">Keduanya</SelectItem>
                    <SelectItem value="none">Tanpa Harga</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Product Selection & Preview */}
        <div className="col-span-9 space-y-4">
          {/* Search & Actions */}
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Cari produk, kode, atau barcode..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-10 bg-[#0a0608] border-red-900/30"
                />
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="border-red-900/30" onClick={selectAll}>
                  Pilih Semua
                </Button>
                <Button variant="outline" size="sm" className="border-red-900/30" onClick={clearSelection}>
                  Batal Pilih
                </Button>
              </div>
              <div className="flex-1" />
              <span className="text-gray-400 text-sm">{selectedItems.length} item dipilih</span>
              <Button 
                onClick={handlePrint} 
                disabled={selectedItems.length === 0}
                className="bg-gradient-to-r from-red-600 to-amber-600"
              >
                <Printer className="h-4 w-4 mr-2" /> Cetak
              </Button>
            </div>
          </div>

          {/* Selected Items with Qty */}
          {selectedItems.length > 0 && (
            <div className="bg-[#1a1214] border border-amber-600/30 rounded-xl p-4">
              <h4 className="text-amber-200 font-semibold mb-3">Item Terpilih untuk Dicetak</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {selectedItems.map(item => (
                  <div key={item.id} className="bg-[#0a0608] border border-red-900/30 rounded-lg p-3">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-200 truncate">{item.name}</p>
                        <p className="text-xs text-amber-400 font-mono">{getBarcodeValue(item)}</p>
                      </div>
                      <button onClick={() => toggleSelectProduct(item)} className="p-1 hover:bg-red-600/20 rounded">
                        <X className="h-4 w-4 text-red-400" />
                      </button>
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-gray-400">Qty:</label>
                      <Input
                        type="number"
                        min="1"
                        max="100"
                        value={item.print_qty}
                        onChange={(e) => updateItemQty(item.id, parseInt(e.target.value) || 1)}
                        className="w-16 h-7 text-xs bg-[#0a0608] border-red-900/30"
                      />
                    </div>
                    {/* Preview */}
                    <div className="mt-2 p-2 bg-white rounded">
                      <svg ref={el => previewRefs.current[item.id] = el} className="w-full" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Product List */}
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
            <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
              <table className="w-full">
                <thead className="bg-red-900/20 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 text-center w-12">
                      <input 
                        type="checkbox"
                        checked={selectedItems.length === filteredProducts.length && filteredProducts.length > 0}
                        onChange={() => selectedItems.length === filteredProducts.length ? clearSelection() : selectAll()}
                        className="w-4 h-4"
                      />
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">BARCODE</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA PRODUK</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">HARGA BELI</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">HARGA JUAL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-red-900/20">
                  {loading ? (
                    <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">Memuat data...</td></tr>
                  ) : filteredProducts.length === 0 ? (
                    <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">Tidak ada produk</td></tr>
                  ) : (
                    filteredProducts.slice(0, 100).map(item => {
                      const isSelected = selectedItems.some(i => i.id === item.id);
                      return (
                        <tr 
                          key={item.id}
                          onClick={() => toggleSelectProduct(item)}
                          className={`cursor-pointer transition-colors ${
                            isSelected ? 'bg-amber-900/20' : 'hover:bg-red-900/10'
                          }`}
                        >
                          <td className="px-4 py-3 text-center">
                            <input 
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleSelectProduct(item)}
                              onClick={(e) => e.stopPropagation()}
                              className="w-4 h-4"
                            />
                          </td>
                          <td className="px-4 py-3 font-mono text-amber-300 text-sm">{item.code}</td>
                          <td className="px-4 py-3 font-mono text-gray-400 text-sm">{item.barcode || item.code}</td>
                          <td className="px-4 py-3 text-gray-200">{item.name}</td>
                          <td className="px-4 py-3 text-right text-gray-400">{formatCurrency(item.cost_price)}</td>
                          <td className="px-4 py-3 text-right text-green-400">{formatCurrency(item.selling_price)}</td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
            {filteredProducts.length > 100 && (
              <div className="p-3 text-center text-gray-400 text-sm border-t border-red-900/20">
                Menampilkan 100 dari {filteredProducts.length} produk
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Template Modal */}
      {showTemplateModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">
                {editingTemplate ? 'Edit Template' : 'Template Baru'}
              </h2>
              <button onClick={() => { setShowTemplateModal(false); resetTemplateForm(); }} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5 text-gray-400" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama Template *</label>
                <Input
                  value={templateForm.template_name}
                  onChange={(e) => setTemplateForm({ ...templateForm, template_name: e.target.value })}
                  className="bg-[#0a0608] border-red-900/30"
                  placeholder="Contoh: Label 50x30"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Lebar (mm)</label>
                  <Input
                    type="number"
                    value={templateForm.width}
                    onChange={(e) => setTemplateForm({ ...templateForm, width: Number(e.target.value) })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tinggi (mm)</label>
                  <Input
                    type="number"
                    value={templateForm.height}
                    onChange={(e) => setTemplateForm({ ...templateForm, height: Number(e.target.value) })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Margin (mm)</label>
                  <Input
                    type="number"
                    value={templateForm.margin}
                    onChange={(e) => setTemplateForm({ ...templateForm, margin: Number(e.target.value) })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Gap (mm)</label>
                  <Input
                    type="number"
                    value={templateForm.gap}
                    onChange={(e) => setTemplateForm({ ...templateForm, gap: Number(e.target.value) })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tipe Barcode</label>
                  <Select 
                    value={templateForm.barcode_type} 
                    onValueChange={(v) => setTemplateForm({ ...templateForm, barcode_type: v })}
                  >
                    <SelectTrigger className="bg-[#0a0608] border-red-900/30">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CODE128">CODE128</SelectItem>
                      <SelectItem value="EAN13">EAN13</SelectItem>
                      <SelectItem value="EAN8">EAN8</SelectItem>
                      <SelectItem value="UPC">UPC</SelectItem>
                      <SelectItem value="CODE39">CODE39</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Ukuran Font</label>
                  <Input
                    type="number"
                    value={templateForm.font_size}
                    onChange={(e) => setTemplateForm({ ...templateForm, font_size: Number(e.target.value) })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
              </div>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={templateForm.show_name}
                    onChange={(e) => setTemplateForm({ ...templateForm, show_name: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-300">Tampilkan Nama</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={templateForm.show_price}
                    onChange={(e) => setTemplateForm({ ...templateForm, show_price: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-300">Tampilkan Harga</span>
                </label>
              </div>
            </div>
            <div className="p-4 border-t border-red-900/30 flex justify-end gap-3">
              <Button variant="outline" className="border-red-900/30" onClick={() => { setShowTemplateModal(false); resetTemplateForm(); }}>
                Batal
              </Button>
              <Button onClick={saveTemplate} className="bg-gradient-to-r from-red-600 to-amber-600">
                <Save className="h-4 w-4 mr-2" /> Simpan
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MasterBarcode;
