import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Switch } from '../../components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Plus, Search, Trash2, Loader2, Printer, Eye, Package, Settings, RefreshCw, Download, X, Barcode } from 'lucide-react';
import { toast } from 'sonner';
import JsBarcode from 'jsbarcode';

const API = process.env.REACT_APP_BACKEND_URL;

// Default templates
const DEFAULT_TEMPLATES = [
  { id: 'kertas_a4', name: 'Kertas A4 (3x8)', paper_type: 'A4', width_mm: 70, height_mm: 37, margin_top: 10, margin_left: 5, gap_horizontal: 0, gap_vertical: 0, cols: 3, rows: 8 },
  { id: 'kertas_58mm', name: 'Thermal 58mm', paper_type: '58mm', width_mm: 58, height_mm: 30, margin_top: 2, margin_left: 2, gap_horizontal: 0, gap_vertical: 2, cols: 1, rows: 1 },
  { id: 'kertas_80mm', name: 'Thermal 80mm', paper_type: '80mm', width_mm: 80, height_mm: 40, margin_top: 2, margin_left: 2, gap_horizontal: 0, gap_vertical: 2, cols: 1, rows: 1 },
  { id: 'label_50x25', name: 'Label 50x25mm', paper_type: 'Label', width_mm: 50, height_mm: 25, margin_top: 0, margin_left: 0, gap_horizontal: 2, gap_vertical: 2, cols: 1, rows: 1 },
  { id: 'label_40x20', name: 'Label 40x20mm', paper_type: 'Label', width_mm: 40, height_mm: 20, margin_top: 0, margin_left: 0, gap_horizontal: 2, gap_vertical: 2, cols: 1, rows: 1 },
];

const MasterBarcodeAdvanced = () => {
  const { api } = useAuth();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Selected items for printing
  const [selectedItems, setSelectedItems] = useState([]);
  
  // Templates
  const [templates, setTemplates] = useState(DEFAULT_TEMPLATES);
  const [selectedTemplate, setSelectedTemplate] = useState(DEFAULT_TEMPLATES[0]);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  
  // Print settings
  const [priceMode, setPriceMode] = useState('sell'); // sell, cost, both
  const [showBarcode, setShowBarcode] = useState(true);
  const [showName, setShowName] = useState(true);
  const [showPrice, setShowPrice] = useState(true);
  const [barcodeType, setBarcodeType] = useState('CODE128'); // CODE128, EAN13, EAN8, UPC
  
  // Preview
  const [showPreview, setShowPreview] = useState(false);
  const previewRef = useRef(null);
  
  // Template form
  const [templateForm, setTemplateForm] = useState({
    name: '',
    paper_type: 'Label',
    width_mm: 50,
    height_mm: 25,
    margin_top: 0,
    margin_left: 0,
    gap_horizontal: 2,
    gap_vertical: 2,
    cols: 1,
    rows: 1,
    font_size_name: 10,
    font_size_price: 12,
    barcode_height: 30
  });

  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/products?search=${searchTerm}&limit=100`);
      if (res.ok) {
        const data = await res.json();
        setProducts(data.items || data || []);
      }
    } catch (err) { 
      toast.error('Gagal memuat data produk'); 
    }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadProducts(); }, [loadProducts]);

  // Load templates from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('barcode_templates');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setTemplates([...DEFAULT_TEMPLATES, ...parsed.filter(t => !DEFAULT_TEMPLATES.find(d => d.id === t.id))]);
      } catch (e) {}
    }
  }, []);

  // Save templates to localStorage
  const saveTemplates = (newTemplates) => {
    const custom = newTemplates.filter(t => !DEFAULT_TEMPLATES.find(d => d.id === t.id));
    localStorage.setItem('barcode_templates', JSON.stringify(custom));
    setTemplates(newTemplates);
  };

  const addItem = (product) => {
    const existing = selectedItems.find(i => i.product_id === product.id);
    if (existing) {
      setSelectedItems(selectedItems.map(i => 
        i.product_id === product.id ? { ...i, quantity: i.quantity + 1 } : i
      ));
    } else {
      setSelectedItems([...selectedItems, {
        product_id: product.id,
        code: product.code,
        name: product.name,
        barcode: product.barcode || product.code,
        cost_price: product.cost_price || 0,
        sell_price: product.selling_price || product.sell_price || 0,
        quantity: 1
      }]);
    }
    toast.success(`${product.name} ditambahkan`);
  };

  const updateQuantity = (productId, qty) => {
    if (qty <= 0) {
      setSelectedItems(selectedItems.filter(i => i.product_id !== productId));
    } else {
      setSelectedItems(selectedItems.map(i => 
        i.product_id === productId ? { ...i, quantity: qty } : i
      ));
    }
  };

  const removeItem = (productId) => {
    setSelectedItems(selectedItems.filter(i => i.product_id !== productId));
  };

  const clearAll = () => {
    setSelectedItems([]);
  };

  const getTotalLabels = () => {
    return selectedItems.reduce((sum, item) => sum + item.quantity, 0);
  };

  // Generate barcode SVG
  const generateBarcodeSVG = (value, width = 150, height = 50) => {
    const canvas = document.createElement('canvas');
    try {
      JsBarcode(canvas, value, {
        format: barcodeType,
        width: 2,
        height: height,
        displayValue: true,
        fontSize: 10,
        margin: 5
      });
      return canvas.toDataURL('image/png');
    } catch (e) {
      // Fallback to CODE128 if format fails
      try {
        JsBarcode(canvas, value, {
          format: 'CODE128',
          width: 2,
          height: height,
          displayValue: true,
          fontSize: 10,
          margin: 5
        });
        return canvas.toDataURL('image/png');
      } catch (e2) {
        return null;
      }
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
  };

  // Handle template save
  const handleSaveTemplate = () => {
    if (!templateForm.name.trim()) {
      toast.error('Nama template wajib diisi');
      return;
    }
    
    const newTemplate = {
      ...templateForm,
      id: editingTemplate?.id || `custom_${Date.now()}`
    };
    
    if (editingTemplate) {
      saveTemplates(templates.map(t => t.id === editingTemplate.id ? newTemplate : t));
    } else {
      saveTemplates([...templates, newTemplate]);
    }
    
    toast.success('Template berhasil disimpan');
    setShowTemplateModal(false);
    setEditingTemplate(null);
  };

  // Handle template delete
  const handleDeleteTemplate = (template) => {
    if (DEFAULT_TEMPLATES.find(t => t.id === template.id)) {
      toast.error('Template default tidak bisa dihapus');
      return;
    }
    if (!window.confirm(`Hapus template "${template.name}"?`)) return;
    saveTemplates(templates.filter(t => t.id !== template.id));
    toast.success('Template dihapus');
  };

  // Generate print preview
  const generatePreviewHTML = () => {
    const labels = [];
    selectedItems.forEach(item => {
      for (let i = 0; i < item.quantity; i++) {
        labels.push(item);
      }
    });

    return labels.map((item, index) => {
      const barcodeImg = generateBarcodeSVG(item.barcode || item.code);
      
      return (
        <div key={index} className="inline-block border border-dashed border-gray-400 p-2 m-1 text-center bg-white"
          style={{ 
            width: `${selectedTemplate.width_mm}mm`, 
            height: `${selectedTemplate.height_mm}mm`,
            fontSize: '10px',
            overflow: 'hidden'
          }}>
          {showName && (
            <div className="font-semibold text-black truncate" style={{ fontSize: `${selectedTemplate.font_size_name || 10}px` }}>
              {item.name}
            </div>
          )}
          {showBarcode && barcodeImg && (
            <img src={barcodeImg} alt="barcode" className="mx-auto" style={{ maxWidth: '100%', height: `${selectedTemplate.barcode_height || 30}px` }} />
          )}
          {showPrice && (
            <div className="font-bold text-black" style={{ fontSize: `${selectedTemplate.font_size_price || 12}px` }}>
              {priceMode === 'cost' ? formatCurrency(item.cost_price) : 
               priceMode === 'both' ? `${formatCurrency(item.cost_price)} / ${formatCurrency(item.sell_price)}` :
               formatCurrency(item.sell_price)}
            </div>
          )}
        </div>
      );
    });
  };

  // Print function
  const handlePrint = () => {
    if (selectedItems.length === 0) {
      toast.error('Pilih item terlebih dahulu');
      return;
    }
    
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      toast.error('Popup diblokir. Izinkan popup untuk mencetak.');
      return;
    }

    const labels = [];
    selectedItems.forEach(item => {
      for (let i = 0; i < item.quantity; i++) {
        labels.push(item);
      }
    });

    const labelsHTML = labels.map(item => {
      const barcodeCanvas = document.createElement('canvas');
      try {
        JsBarcode(barcodeCanvas, item.barcode || item.code, {
          format: barcodeType,
          width: 2,
          height: selectedTemplate.barcode_height || 30,
          displayValue: true,
          fontSize: 10,
          margin: 5
        });
      } catch (e) {
        JsBarcode(barcodeCanvas, item.barcode || item.code, {
          format: 'CODE128',
          width: 2,
          height: selectedTemplate.barcode_height || 30,
          displayValue: true,
          fontSize: 10,
          margin: 5
        });
      }
      
      return `
        <div class="label" style="
          width: ${selectedTemplate.width_mm}mm;
          height: ${selectedTemplate.height_mm}mm;
          display: inline-block;
          border: 1px dashed #ccc;
          padding: 2mm;
          margin: 1mm;
          text-align: center;
          overflow: hidden;
          box-sizing: border-box;
          page-break-inside: avoid;
        ">
          ${showName ? `<div style="font-weight: bold; font-size: ${selectedTemplate.font_size_name || 10}px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${item.name}</div>` : ''}
          ${showBarcode ? `<img src="${barcodeCanvas.toDataURL('image/png')}" style="max-width: 100%; height: ${selectedTemplate.barcode_height || 30}px;" />` : ''}
          ${showPrice ? `<div style="font-weight: bold; font-size: ${selectedTemplate.font_size_price || 12}px;">
            ${priceMode === 'cost' ? formatCurrency(item.cost_price) : 
             priceMode === 'both' ? `${formatCurrency(item.cost_price)} / ${formatCurrency(item.sell_price)}` :
             formatCurrency(item.sell_price)}
          </div>` : ''}
        </div>
      `;
    }).join('');

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Cetak Barcode</title>
        <style>
          @page { margin: ${selectedTemplate.margin_top}mm ${selectedTemplate.margin_left}mm; }
          body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
          .container { display: flex; flex-wrap: wrap; }
        </style>
      </head>
      <body>
        <div class="container">${labelsHTML}</div>
        <script>window.onload = function() { window.print(); }</script>
      </body>
      </html>
    `);
    printWindow.document.close();
  };

  return (
    <div className="space-y-4" data-testid="barcode-advanced-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Cetak Barcode</h1>
          <p className="text-gray-400 text-sm">Cetak label barcode untuk produk dengan berbagai template</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => { 
            setEditingTemplate(null); 
            setTemplateForm({ name: '', paper_type: 'Label', width_mm: 50, height_mm: 25, margin_top: 0, margin_left: 0, gap_horizontal: 2, gap_vertical: 2, cols: 1, rows: 1, font_size_name: 10, font_size_price: 12, barcode_height: 30 });
            setShowTemplateModal(true); 
          }}>
            <Settings className="h-4 w-4 mr-2" /> Kelola Template
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* Left: Product List */}
        <div className="col-span-2 space-y-4">
          <Card className="bg-[#1a1214] border-red-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                <Package className="h-4 w-4" /> Daftar Produk
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input type="text" placeholder="Cari produk..." value={searchTerm} 
                    onChange={(e) => setSearchTerm(e.target.value)} 
                    className="pl-10 bg-[#0a0608] border-red-900/30" />
                </div>
                <Button variant="outline" onClick={loadProducts}><RefreshCw className="h-4 w-4" /></Button>
              </div>
              
              <div className="max-h-[400px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-red-900/20 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left text-amber-200">Kode</th>
                      <th className="px-3 py-2 text-left text-amber-200">Nama Produk</th>
                      <th className="px-3 py-2 text-left text-amber-200">Barcode</th>
                      <th className="px-3 py-2 text-right text-amber-200">Harga</th>
                      <th className="px-3 py-2 text-center text-amber-200">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-900/20">
                    {loading ? (
                      <tr><td colSpan={5} className="py-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto text-amber-400" /></td></tr>
                    ) : products.length === 0 ? (
                      <tr><td colSpan={5} className="py-8 text-center text-gray-400">Tidak ada produk</td></tr>
                    ) : products.map(product => (
                      <tr key={product.id} className="hover:bg-red-900/10">
                        <td className="px-3 py-2 font-mono text-amber-300 text-xs">{product.code}</td>
                        <td className="px-3 py-2 text-gray-200">{product.name}</td>
                        <td className="px-3 py-2 text-gray-400 text-xs">{product.barcode || product.code}</td>
                        <td className="px-3 py-2 text-right text-gray-300">{formatCurrency(product.selling_price || product.sell_price)}</td>
                        <td className="px-3 py-2 text-center">
                          <Button size="sm" onClick={() => addItem(product)} className="bg-green-600 hover:bg-green-700 h-7">
                            <Plus className="h-3 w-3" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: Selected Items & Settings */}
        <div className="space-y-4">
          {/* Print Settings */}
          <Card className="bg-[#1a1214] border-red-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                <Settings className="h-4 w-4" /> Pengaturan Cetak
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-gray-300 text-xs">Template</Label>
                <Select value={selectedTemplate.id} onValueChange={(v) => setSelectedTemplate(templates.find(t => t.id === v) || templates[0])}>
                  <SelectTrigger className="bg-[#0a0608] border-red-900/30 h-8 text-sm"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {templates.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label className="text-gray-300 text-xs">Tampilan Harga</Label>
                <Select value={priceMode} onValueChange={setPriceMode}>
                  <SelectTrigger className="bg-[#0a0608] border-red-900/30 h-8 text-sm"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sell">Harga Jual</SelectItem>
                    <SelectItem value="cost">Harga Beli</SelectItem>
                    <SelectItem value="both">Keduanya</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label className="text-gray-300 text-xs">Tipe Barcode</Label>
                <Select value={barcodeType} onValueChange={setBarcodeType}>
                  <SelectTrigger className="bg-[#0a0608] border-red-900/30 h-8 text-sm"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CODE128">CODE128</SelectItem>
                    <SelectItem value="EAN13">EAN13</SelectItem>
                    <SelectItem value="EAN8">EAN8</SelectItem>
                    <SelectItem value="UPC">UPC</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Switch checked={showName} onCheckedChange={setShowName} />
                  <Label className="text-gray-300 text-xs">Tampilkan Nama</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={showBarcode} onCheckedChange={setShowBarcode} />
                  <Label className="text-gray-300 text-xs">Tampilkan Barcode</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={showPrice} onCheckedChange={setShowPrice} />
                  <Label className="text-gray-300 text-xs">Tampilkan Harga</Label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Selected Items */}
          <Card className="bg-[#1a1214] border-red-900/30">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Barcode className="h-4 w-4" /> Item Dipilih ({getTotalLabels()} label)
                </CardTitle>
                {selectedItems.length > 0 && (
                  <Button size="sm" variant="ghost" onClick={clearAll} className="text-red-400 h-6 text-xs">
                    Hapus Semua
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {selectedItems.length === 0 ? (
                <p className="text-gray-400 text-sm text-center py-4">Belum ada item dipilih</p>
              ) : (
                <div className="space-y-2 max-h-[200px] overflow-y-auto">
                  {selectedItems.map(item => (
                    <div key={item.product_id} className="flex items-center justify-between bg-[#0a0608] p-2 rounded">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-gray-200 truncate">{item.name}</div>
                        <div className="text-xs text-gray-500">{item.code}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Input type="number" value={item.quantity} 
                          onChange={(e) => updateQuantity(item.product_id, parseInt(e.target.value) || 0)}
                          className="w-16 h-7 text-center bg-[#1a1214] border-red-900/30 text-sm" min="0" />
                        <Button size="sm" variant="ghost" onClick={() => removeItem(item.product_id)} className="text-red-400 h-7 w-7 p-0">
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              <div className="flex gap-2 mt-4">
                <Button onClick={() => setShowPreview(true)} variant="outline" className="flex-1" disabled={selectedItems.length === 0}>
                  <Eye className="h-4 w-4 mr-2" /> Preview
                </Button>
                <Button onClick={handlePrint} className="flex-1 bg-gradient-to-r from-red-600 to-amber-600" disabled={selectedItems.length === 0} data-testid="print-barcode-btn">
                  <Printer className="h-4 w-4 mr-2" /> Cetak
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Preview Modal */}
      <Dialog open={showPreview} onOpenChange={setShowPreview}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-white">
          <DialogHeader>
            <DialogTitle className="text-gray-900">Preview Barcode ({getTotalLabels()} label)</DialogTitle>
          </DialogHeader>
          <div className="p-4 bg-gray-100 rounded-lg" ref={previewRef}>
            <div className="flex flex-wrap">
              {generatePreviewHTML()}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPreview(false)}>Tutup</Button>
            <Button onClick={handlePrint} className="bg-blue-600 hover:bg-blue-700">
              <Printer className="h-4 w-4 mr-2" /> Cetak Sekarang
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Template Modal */}
      <Dialog open={showTemplateModal} onOpenChange={setShowTemplateModal}>
        <DialogContent className="max-w-2xl bg-[#1a1214] border-red-900/30">
          <DialogHeader>
            <DialogTitle className="text-amber-100">{editingTemplate ? 'Edit' : 'Tambah'} Template</DialogTitle>
          </DialogHeader>
          <Tabs defaultValue="list">
            <TabsList className="bg-[#0a0608]">
              <TabsTrigger value="list">Daftar Template</TabsTrigger>
              <TabsTrigger value="form">{editingTemplate ? 'Edit' : 'Tambah'} Template</TabsTrigger>
            </TabsList>
            
            <TabsContent value="list" className="space-y-2 mt-4">
              {templates.map(template => (
                <div key={template.id} className="flex items-center justify-between bg-[#0a0608] p-3 rounded-lg">
                  <div>
                    <div className="text-gray-200 font-medium">{template.name}</div>
                    <div className="text-xs text-gray-500">{template.width_mm}mm × {template.height_mm}mm</div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="ghost" onClick={() => {
                      setEditingTemplate(template);
                      setTemplateForm(template);
                    }} className="text-blue-400">Edit</Button>
                    {!DEFAULT_TEMPLATES.find(t => t.id === template.id) && (
                      <Button size="sm" variant="ghost" onClick={() => handleDeleteTemplate(template)} className="text-red-400">Hapus</Button>
                    )}
                  </div>
                </div>
              ))}
            </TabsContent>
            
            <TabsContent value="form" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-300">Nama Template</Label>
                  <Input value={templateForm.name} onChange={(e) => setTemplateForm({...templateForm, name: e.target.value})}
                    className="bg-[#0a0608] border-red-900/30" placeholder="Nama template" />
                </div>
                <div>
                  <Label className="text-gray-300">Jenis Kertas</Label>
                  <Select value={templateForm.paper_type} onValueChange={(v) => setTemplateForm({...templateForm, paper_type: v})}>
                    <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="A4">A4</SelectItem>
                      <SelectItem value="58mm">Thermal 58mm</SelectItem>
                      <SelectItem value="80mm">Thermal 80mm</SelectItem>
                      <SelectItem value="Label">Label</SelectItem>
                      <SelectItem value="Custom">Custom</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-300">Lebar (mm)</Label>
                  <Input type="number" value={templateForm.width_mm} 
                    onChange={(e) => setTemplateForm({...templateForm, width_mm: parseInt(e.target.value) || 0})}
                    className="bg-[#0a0608] border-red-900/30" />
                </div>
                <div>
                  <Label className="text-gray-300">Tinggi (mm)</Label>
                  <Input type="number" value={templateForm.height_mm} 
                    onChange={(e) => setTemplateForm({...templateForm, height_mm: parseInt(e.target.value) || 0})}
                    className="bg-[#0a0608] border-red-900/30" />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-300">Margin Atas (mm)</Label>
                  <Input type="number" value={templateForm.margin_top} 
                    onChange={(e) => setTemplateForm({...templateForm, margin_top: parseInt(e.target.value) || 0})}
                    className="bg-[#0a0608] border-red-900/30" />
                </div>
                <div>
                  <Label className="text-gray-300">Margin Kiri (mm)</Label>
                  <Input type="number" value={templateForm.margin_left} 
                    onChange={(e) => setTemplateForm({...templateForm, margin_left: parseInt(e.target.value) || 0})}
                    className="bg-[#0a0608] border-red-900/30" />
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label className="text-gray-300">Font Nama (px)</Label>
                  <Input type="number" value={templateForm.font_size_name} 
                    onChange={(e) => setTemplateForm({...templateForm, font_size_name: parseInt(e.target.value) || 10})}
                    className="bg-[#0a0608] border-red-900/30" />
                </div>
                <div>
                  <Label className="text-gray-300">Font Harga (px)</Label>
                  <Input type="number" value={templateForm.font_size_price} 
                    onChange={(e) => setTemplateForm({...templateForm, font_size_price: parseInt(e.target.value) || 12})}
                    className="bg-[#0a0608] border-red-900/30" />
                </div>
                <div>
                  <Label className="text-gray-300">Tinggi Barcode (px)</Label>
                  <Input type="number" value={templateForm.barcode_height} 
                    onChange={(e) => setTemplateForm({...templateForm, barcode_height: parseInt(e.target.value) || 30})}
                    className="bg-[#0a0608] border-red-900/30" />
                </div>
              </div>
              
              <Button onClick={handleSaveTemplate} className="w-full bg-gradient-to-r from-red-600 to-amber-600">
                Simpan Template
              </Button>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MasterBarcodeAdvanced;
