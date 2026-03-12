import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Switch } from '../../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { toast } from 'sonner';
import { 
  Plus, Search, Edit, Trash2, Save, X, Barcode, Printer, 
  FileText, Settings, Eye, Download, RefreshCw, ChevronLeft,
  Package, Minus
} from 'lucide-react';
import JsBarcode from 'jsbarcode';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const PAPER_SIZES = [
  { value: 'label_58x40', label: 'Label 58x40mm', width: 58, height: 40, cols: 1, rows: 1 },
  { value: 'label_38x25', label: 'Label 38x25mm', width: 38, height: 25, cols: 1, rows: 1 },
  { value: 'a4_30', label: 'A4 - 30 Label (3x10)', width: 70, height: 29.7, cols: 3, rows: 10 },
  { value: 'a4_65', label: 'A4 - 65 Label (5x13)', width: 38.1, height: 21.2, cols: 5, rows: 13 },
  { value: 'custom', label: 'Custom', width: 50, height: 30, cols: 1, rows: 1 },
];

const BARCODE_TYPES = [
  { value: 'code128', label: 'Code 128' },
  { value: 'ean13', label: 'EAN-13' },
  { value: 'code39', label: 'Code 39' },
  { value: 'upc', label: 'UPC' },
];

const BARCODE_SOURCES = [
  { value: 'barcode', label: 'Field Barcode' },
  { value: 'item_code', label: 'Kode Item' },
  { value: 'sku', label: 'SKU' },
];

const MasterBarcodeAdvanced = () => {
  const [activeTab, setActiveTab] = useState('print');
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState([]);
  const [searchItem, setSearchItem] = useState('');
  const printRef = useRef(null);
  
  // Template form
  const [showTemplateForm, setShowTemplateForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [templateForm, setTemplateForm] = useState({
    code: '',
    name: '',
    paper_size: 'label_58x40',
    width_mm: 58,
    height_mm: 40,
    columns: 1,
    rows: 1,
    margin_top: 2,
    margin_bottom: 2,
    margin_left: 2,
    margin_right: 2,
    gap_h: 2,
    gap_v: 2,
    barcode_type: 'code128',
    barcode_source: 'barcode',
    show_item_name: true,
    show_item_code: true,
    show_price: true,
    price_type: 'sell',
    font_size: 10,
    barcode_height: 15,
    is_active: true,
    notes: ''
  });
  
  // Print state
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedItems, setSelectedItems] = useState([]);  // [{item_id, item_code, item_name, qty, barcode, price}]
  const [previewData, setPreviewData] = useState(null);

  const fetchTemplates = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/master-advanced/barcode-templates`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setTemplates(data.items || []);
      if (data.items?.length > 0 && !selectedTemplate) {
        setSelectedTemplate(data.items[0].id);
      }
    } catch (err) {
      console.error('Error fetching templates:', err);
    }
  };

  const fetchItems = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (searchItem) params.append('search', searchItem);
      params.append('limit', '50');
      
      const res = await fetch(`${API_URL}/api/master-erp/items?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setItems(data.items || []);
    } catch (err) {
      console.error('Error fetching items:', err);
    }
  }, [searchItem]);

  useEffect(() => {
    fetchTemplates();
    fetchItems();
  }, [fetchItems]);

  const handlePaperSizeChange = (value) => {
    const size = PAPER_SIZES.find(p => p.value === value);
    if (size) {
      setTemplateForm(prev => ({
        ...prev,
        paper_size: value,
        width_mm: size.width,
        height_mm: size.height,
        columns: size.cols,
        rows: size.rows
      }));
    }
  };

  const handleTemplateInputChange = (field, value) => {
    setTemplateForm(prev => ({ ...prev, [field]: value }));
  };

  const resetTemplateForm = () => {
    setTemplateForm({
      code: '',
      name: '',
      paper_size: 'label_58x40',
      width_mm: 58,
      height_mm: 40,
      columns: 1,
      rows: 1,
      margin_top: 2,
      margin_bottom: 2,
      margin_left: 2,
      margin_right: 2,
      gap_h: 2,
      gap_v: 2,
      barcode_type: 'code128',
      barcode_source: 'barcode',
      show_item_name: true,
      show_item_code: true,
      show_price: true,
      price_type: 'sell',
      font_size: 10,
      barcode_height: 15,
      is_active: true,
      notes: ''
    });
    setEditingTemplate(null);
  };

  const handleSaveTemplate = async () => {
    if (!templateForm.name.trim()) {
      toast.error('Nama template wajib diisi');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const url = editingTemplate 
        ? `${API_URL}/api/master-advanced/barcode-templates/${editingTemplate.id}`
        : `${API_URL}/api/master-advanced/barcode-templates`;
      
      const res = await fetch(url, {
        method: editingTemplate ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(templateForm)
      });

      const data = await res.json();
      
      if (res.ok && data.success) {
        toast.success(editingTemplate ? 'Template berhasil diupdate' : 'Template berhasil dibuat');
        setShowTemplateForm(false);
        resetTemplateForm();
        fetchTemplates();
      } else {
        toast.error(data.detail || 'Gagal menyimpan template');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const handleDeleteTemplate = async (template) => {
    if (!window.confirm(`Hapus template "${template.name}"?`)) return;
    
    try {
      const token = localStorage.getItem('token');
      await fetch(`${API_URL}/api/master-advanced/barcode-templates/${template.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      toast.success('Template berhasil dihapus');
      fetchTemplates();
    } catch (err) {
      toast.error('Gagal menghapus template');
    }
  };

  const openEditTemplate = (template) => {
    setTemplateForm({
      code: template.code || '',
      name: template.name || '',
      paper_size: template.paper_size || 'label_58x40',
      width_mm: template.width_mm || 58,
      height_mm: template.height_mm || 40,
      columns: template.columns || 1,
      rows: template.rows || 1,
      margin_top: template.margin_top || 2,
      margin_bottom: template.margin_bottom || 2,
      margin_left: template.margin_left || 2,
      margin_right: template.margin_right || 2,
      gap_h: template.gap_h || 2,
      gap_v: template.gap_v || 2,
      barcode_type: template.barcode_type || 'code128',
      barcode_source: template.barcode_source || 'barcode',
      show_item_name: template.show_item_name !== false,
      show_item_code: template.show_item_code !== false,
      show_price: template.show_price !== false,
      price_type: template.price_type || 'sell',
      font_size: template.font_size || 10,
      barcode_height: template.barcode_height || 15,
      is_active: template.is_active !== false,
      notes: template.notes || ''
    });
    setEditingTemplate(template);
    setShowTemplateForm(true);
  };

  const addItemToPrint = (item) => {
    const existing = selectedItems.find(i => i.item_id === item.id);
    if (existing) {
      setSelectedItems(prev => prev.map(i => 
        i.item_id === item.id ? { ...i, qty: i.qty + 1 } : i
      ));
    } else {
      setSelectedItems(prev => [...prev, {
        item_id: item.id,
        item_code: item.code,
        item_name: item.name,
        qty: 1,
        barcode: item.barcode || item.code,
        price: item.sell_price || 0
      }]);
    }
  };

  const updateItemQty = (item_id, qty) => {
    if (qty <= 0) {
      setSelectedItems(prev => prev.filter(i => i.item_id !== item_id));
    } else {
      setSelectedItems(prev => prev.map(i => 
        i.item_id === item_id ? { ...i, qty } : i
      ));
    }
  };

  const removeItem = (item_id) => {
    setSelectedItems(prev => prev.filter(i => i.item_id !== item_id));
  };

  const generatePreview = async () => {
    if (selectedItems.length === 0) {
      toast.error('Pilih item terlebih dahulu');
      return;
    }
    if (!selectedTemplate) {
      toast.error('Pilih template terlebih dahulu');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/master-advanced/barcode/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          template_id: selectedTemplate,
          items: selectedItems.map(i => ({ item_id: i.item_id, qty: i.qty }))
        })
      });

      const data = await res.json();
      if (data.success) {
        setPreviewData(data);
        toast.success(`Preview ${data.total_labels} label`);
      }
    } catch (err) {
      toast.error('Gagal generate preview');
    }
  };

  const handlePrint = () => {
    if (!previewData) {
      toast.error('Generate preview terlebih dahulu');
      return;
    }

    const printWindow = window.open('', '_blank');
    const template = templates.find(t => t.id === selectedTemplate) || {};
    
    const labelWidth = template.width_mm || 58;
    const labelHeight = template.height_mm || 40;
    const fontSize = template.font_size || 10;
    const barcodeHeight = template.barcode_height || 15;
    
    let html = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Print Barcode</title>
        <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
        <style>
          @page { size: auto; margin: 2mm; }
          body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
          .label-container { display: flex; flex-wrap: wrap; }
          .label {
            width: ${labelWidth}mm;
            height: ${labelHeight}mm;
            padding: 2mm;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 1px dashed #ccc;
            page-break-inside: avoid;
          }
          .item-name { font-size: ${fontSize}px; font-weight: bold; text-align: center; margin-bottom: 2px; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
          .item-code { font-size: ${fontSize - 2}px; color: #666; margin-bottom: 2px; }
          .barcode-svg { max-width: 100%; height: ${barcodeHeight}mm; }
          .price { font-size: ${fontSize}px; font-weight: bold; margin-top: 2px; }
          @media print {
            .label { border: none; }
          }
        </style>
      </head>
      <body>
        <div class="label-container">
    `;
    
    previewData.labels.forEach((label, index) => {
      html += `
        <div class="label">
          ${template.show_item_name !== false ? `<div class="item-name">${label.item_name}</div>` : ''}
          ${template.show_item_code !== false ? `<div class="item-code">${label.item_code}</div>` : ''}
          <svg class="barcode-svg" id="barcode-${index}"></svg>
          ${template.show_price !== false ? `<div class="price">Rp ${new Intl.NumberFormat('id-ID').format(label.price)}</div>` : ''}
        </div>
      `;
    });
    
    html += `
        </div>
        <script>
          window.onload = function() {
    `;
    
    previewData.labels.forEach((label, index) => {
      html += `
            JsBarcode("#barcode-${index}", "${label.barcode_value}", {
              format: "${template.barcode_type || 'CODE128'}",
              width: 1.5,
              height: 30,
              displayValue: true,
              fontSize: 10,
              margin: 0
            });
      `;
    });
    
    html += `
            setTimeout(function() { window.print(); }, 500);
          };
        </script>
      </body>
      </html>
    `;
    
    printWindow.document.write(html);
    printWindow.document.close();
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
  };

  return (
    <div className="p-4 space-y-4" data-testid="barcode-advanced-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Barcode className="h-6 w-6" />
            Cetak Barcode
          </h1>
          <p className="text-gray-500">Cetak label barcode untuk produk</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="print" className="flex items-center gap-1">
            <Printer className="h-4 w-4" />
            Cetak Label
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-1">
            <Settings className="h-4 w-4" />
            Template
          </TabsTrigger>
        </TabsList>

        {/* Tab: Cetak Label */}
        <TabsContent value="print" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Item Selection */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-lg">Pilih Item</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Cari item..."
                    value={searchItem}
                    onChange={(e) => setSearchItem(e.target.value)}
                    className="pl-10"
                    data-testid="search-item-barcode"
                  />
                </div>
                
                <div className="max-h-96 overflow-y-auto space-y-2">
                  {items.map(item => (
                    <div 
                      key={item.id} 
                      className="flex items-center justify-between p-2 border rounded hover:bg-gray-50 cursor-pointer"
                      onClick={() => addItemToPrint(item)}
                      data-testid={`item-${item.id}`}
                    >
                      <div>
                        <div className="font-medium text-sm">{item.code}</div>
                        <div className="text-xs text-gray-500 truncate max-w-[180px]">{item.name}</div>
                      </div>
                      <Button size="sm" variant="ghost">
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Selected Items */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-lg">Item Dipilih</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Template</Label>
                  <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
                    <SelectTrigger data-testid="select-template">
                      <SelectValue placeholder="Pilih template" />
                    </SelectTrigger>
                    <SelectContent>
                      {templates.map(t => (
                        <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="max-h-64 overflow-y-auto space-y-2">
                  {selectedItems.length === 0 ? (
                    <p className="text-sm text-gray-500 text-center py-4">Belum ada item dipilih</p>
                  ) : (
                    selectedItems.map(item => (
                      <div key={item.item_id} className="flex items-center justify-between p-2 border rounded">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{item.item_code}</div>
                          <div className="text-xs text-gray-500 truncate max-w-[150px]">{item.item_name}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button 
                            size="sm" 
                            variant="ghost"
                            onClick={() => updateItemQty(item.item_id, item.qty - 1)}
                          >
                            <Minus className="h-3 w-3" />
                          </Button>
                          <Input
                            type="number"
                            value={item.qty}
                            onChange={(e) => updateItemQty(item.item_id, parseInt(e.target.value) || 0)}
                            className="w-14 text-center h-8"
                            data-testid={`qty-${item.item_id}`}
                          />
                          <Button 
                            size="sm" 
                            variant="ghost"
                            onClick={() => updateItemQty(item.item_id, item.qty + 1)}
                          >
                            <Plus className="h-3 w-3" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="ghost"
                            className="text-red-500"
                            onClick={() => removeItem(item.item_id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="flex items-center justify-between pt-2 border-t">
                  <span className="text-sm font-medium">
                    Total Label: {selectedItems.reduce((sum, i) => sum + i.qty, 0)}
                  </span>
                </div>

                <div className="flex gap-2">
                  <Button className="flex-1" onClick={generatePreview} data-testid="generate-preview-btn">
                    <Eye className="h-4 w-4 mr-1" />
                    Preview
                  </Button>
                  <Button className="flex-1" onClick={handlePrint} disabled={!previewData} data-testid="print-barcode-btn">
                    <Printer className="h-4 w-4 mr-1" />
                    Cetak
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Preview */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-lg">Preview</CardTitle>
              </CardHeader>
              <CardContent>
                {previewData ? (
                  <div className="space-y-2 max-h-96 overflow-y-auto" ref={printRef}>
                    {previewData.labels.slice(0, 10).map((label, index) => {
                      const template = previewData.template || {};
                      return (
                        <div 
                          key={index} 
                          className="border p-2 rounded text-center"
                          style={{ width: `${Math.min(template.width_mm || 58, 100)}mm` }}
                        >
                          {template.show_item_name !== false && (
                            <div className="font-bold text-sm truncate">{label.item_name}</div>
                          )}
                          {template.show_item_code !== false && (
                            <div className="text-xs text-gray-500">{label.item_code}</div>
                          )}
                          <svg 
                            className="mx-auto my-1"
                            ref={(el) => {
                              if (el) {
                                try {
                                  JsBarcode(el, label.barcode_value, {
                                    format: template.barcode_type?.toUpperCase() || 'CODE128',
                                    width: 1,
                                    height: 25,
                                    displayValue: true,
                                    fontSize: 8,
                                    margin: 0
                                  });
                                } catch (e) {
                                  console.error('Barcode error:', e);
                                }
                              }
                            }}
                          />
                          {template.show_price !== false && (
                            <div className="font-bold text-sm">{formatCurrency(label.price)}</div>
                          )}
                        </div>
                      );
                    })}
                    {previewData.labels.length > 10 && (
                      <p className="text-center text-gray-500 text-sm">
                        ... dan {previewData.labels.length - 10} label lainnya
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    Klik "Preview" untuk melihat label
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab: Templates */}
        <TabsContent value="templates" className="space-y-4">
          {showTemplateForm ? (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-4">
                  <Button variant="ghost" size="sm" onClick={() => { setShowTemplateForm(false); resetTemplateForm(); }}>
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Kembali
                  </Button>
                  <CardTitle>{editingTemplate ? 'Edit Template' : 'Tambah Template'}</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label>Kode Template</Label>
                    <Input
                      value={templateForm.code}
                      onChange={(e) => handleTemplateInputChange('code', e.target.value)}
                      placeholder="Auto jika kosong"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Label>Nama Template *</Label>
                    <Input
                      value={templateForm.name}
                      onChange={(e) => handleTemplateInputChange('name', e.target.value)}
                      placeholder="Nama template"
                      data-testid="template-name-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <Label>Ukuran Kertas</Label>
                    <Select value={templateForm.paper_size} onValueChange={handlePaperSizeChange}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PAPER_SIZES.map(p => (
                          <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Lebar (mm)</Label>
                    <Input
                      type="number"
                      value={templateForm.width_mm}
                      onChange={(e) => handleTemplateInputChange('width_mm', parseFloat(e.target.value) || 0)}
                    />
                  </div>
                  <div>
                    <Label>Tinggi (mm)</Label>
                    <Input
                      type="number"
                      value={templateForm.height_mm}
                      onChange={(e) => handleTemplateInputChange('height_mm', parseFloat(e.target.value) || 0)}
                    />
                  </div>
                  <div>
                    <Label>Kolom x Baris</Label>
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        value={templateForm.columns}
                        onChange={(e) => handleTemplateInputChange('columns', parseInt(e.target.value) || 1)}
                        className="w-20"
                      />
                      <span className="flex items-center">x</span>
                      <Input
                        type="number"
                        value={templateForm.rows}
                        onChange={(e) => handleTemplateInputChange('rows', parseInt(e.target.value) || 1)}
                        className="w-20"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label>Tipe Barcode</Label>
                    <Select value={templateForm.barcode_type} onValueChange={(v) => handleTemplateInputChange('barcode_type', v)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {BARCODE_TYPES.map(t => (
                          <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Sumber Barcode</Label>
                    <Select value={templateForm.barcode_source} onValueChange={(v) => handleTemplateInputChange('barcode_source', v)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {BARCODE_SOURCES.map(s => (
                          <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Tipe Harga</Label>
                    <Select value={templateForm.price_type} onValueChange={(v) => handleTemplateInputChange('price_type', v)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="sell">Harga Jual</SelectItem>
                        <SelectItem value="hpp">HPP</SelectItem>
                        <SelectItem value="both">Keduanya</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <Label>Font Size</Label>
                    <Input
                      type="number"
                      value={templateForm.font_size}
                      onChange={(e) => handleTemplateInputChange('font_size', parseInt(e.target.value) || 10)}
                    />
                  </div>
                  <div>
                    <Label>Tinggi Barcode (mm)</Label>
                    <Input
                      type="number"
                      value={templateForm.barcode_height}
                      onChange={(e) => handleTemplateInputChange('barcode_height', parseFloat(e.target.value) || 15)}
                    />
                  </div>
                </div>

                <div className="flex flex-wrap gap-4">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={templateForm.show_item_name}
                      onCheckedChange={(v) => handleTemplateInputChange('show_item_name', v)}
                    />
                    <Label>Tampilkan Nama Item</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={templateForm.show_item_code}
                      onCheckedChange={(v) => handleTemplateInputChange('show_item_code', v)}
                    />
                    <Label>Tampilkan Kode Item</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={templateForm.show_price}
                      onCheckedChange={(v) => handleTemplateInputChange('show_price', v)}
                    />
                    <Label>Tampilkan Harga</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={templateForm.is_active}
                      onCheckedChange={(v) => handleTemplateInputChange('is_active', v)}
                    />
                    <Label>Aktif</Label>
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-4 border-t">
                  <Button variant="outline" onClick={() => { setShowTemplateForm(false); resetTemplateForm(); }}>
                    <X className="h-4 w-4 mr-1" />
                    Batal
                  </Button>
                  <Button onClick={handleSaveTemplate} data-testid="save-template-btn">
                    <Save className="h-4 w-4 mr-1" />
                    {editingTemplate ? 'Update' : 'Simpan'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              <div className="flex justify-end">
                <Button onClick={() => setShowTemplateForm(true)} data-testid="add-template-btn">
                  <Plus className="h-4 w-4 mr-1" />
                  Tambah Template
                </Button>
              </div>

              <Card>
                <CardContent className="p-0">
                  {templates.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                      Belum ada template barcode
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kode</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nama</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ukuran</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipe Barcode</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Aksi</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {templates.map((template) => (
                            <tr key={template.id} className="hover:bg-gray-50">
                              <td className="px-4 py-3 text-sm font-medium">{template.code}</td>
                              <td className="px-4 py-3">{template.name}</td>
                              <td className="px-4 py-3 text-sm">
                                {template.width_mm}x{template.height_mm}mm
                                {template.columns > 1 && ` (${template.columns}x${template.rows})`}
                              </td>
                              <td className="px-4 py-3">
                                <Badge variant="outline">{template.barcode_type?.toUpperCase()}</Badge>
                              </td>
                              <td className="px-4 py-3">
                                {template.is_active !== false ? (
                                  <Badge className="bg-green-100 text-green-800">Aktif</Badge>
                                ) : (
                                  <Badge variant="destructive">Nonaktif</Badge>
                                )}
                              </td>
                              <td className="px-4 py-3 text-center">
                                <div className="flex items-center justify-center gap-1">
                                  <Button 
                                    size="sm" 
                                    variant="ghost" 
                                    onClick={() => openEditTemplate(template)}
                                  >
                                    <Edit className="h-4 w-4" />
                                  </Button>
                                  <Button 
                                    size="sm" 
                                    variant="ghost"
                                    className="text-red-500 hover:text-red-700"
                                    onClick={() => handleDeleteTemplate(template)}
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </Button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MasterBarcodeAdvanced;
