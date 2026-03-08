import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Printer, Settings, Check, TestTube, Save, RefreshCw, Usb, Bluetooth,
  Wifi, Monitor, FileText, Image, AlignLeft, AlignCenter, AlignRight
} from 'lucide-react';
import { toast } from 'sonner';

const PrinterSettings = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(false);
  const [testPrinting, setTestPrinting] = useState(false);
  
  const [settings, setSettings] = useState({
    // Printer Connection
    printer_type: 'thermal', // thermal, inkjet, laser
    connection_type: 'usb', // usb, bluetooth, network
    printer_name: '',
    ip_address: '',
    port: 9100,
    bluetooth_address: '',
    
    // Paper Settings
    paper_width: 80, // mm: 58, 80
    auto_cut: true,
    open_drawer: false,
    
    // Receipt Layout
    header_logo: true,
    header_text: 'OCB AI TITAN',
    header_subtitle: 'Enterprise Retail System',
    header_address: '',
    header_phone: '',
    
    footer_text: 'Terima kasih atas kunjungan Anda',
    footer_note: '',
    
    // Print Options
    print_copies: 1,
    font_size: 'normal', // small, normal, large
    show_logo: true,
    show_barcode: true,
    show_qr_code: false
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const res = await api('/api/settings/printer');
      if (res.ok) {
        const data = await res.json();
        if (data) setSettings(prev => ({ ...prev, ...data }));
      }
    } catch (err) {
      console.error('Error loading printer settings');
    }
  };

  const saveSettings = async () => {
    setLoading(true);
    try {
      const res = await api('/api/settings/printer', {
        method: 'POST',
        body: JSON.stringify(settings)
      });
      if (res.ok) {
        toast.success('Pengaturan printer berhasil disimpan');
      }
    } catch (err) {
      toast.error('Gagal menyimpan pengaturan');
    } finally {
      setLoading(false);
    }
  };

  const testPrint = async () => {
    setTestPrinting(true);
    try {
      const res = await api('/api/settings/printer/test', { method: 'POST' });
      if (res.ok) {
        toast.success('Test print berhasil dikirim!');
      } else {
        toast.error('Test print gagal');
      }
    } catch (err) {
      toast.error('Error saat test print');
    } finally {
      setTestPrinting(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="printer-settings-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Pengaturan Printer & Struk</h1>
          <p className="text-gray-400 text-sm">Konfigurasi printer dan tampilan struk</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={testPrint}
            disabled={testPrinting}
            className="px-4 py-2 bg-blue-600/20 text-blue-400 rounded-lg flex items-center gap-2 hover:bg-blue-600/30"
          >
            {testPrinting ? <RefreshCw className="h-4 w-4 animate-spin" /> : <TestTube className="h-4 w-4" />}
            Test Print
          </button>
          <button 
            onClick={saveSettings}
            disabled={loading}
            className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2"
          >
            <Save className="h-4 w-4" /> Simpan
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Printer Connection */}
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-amber-200 mb-4 flex items-center gap-2">
            <Printer className="h-5 w-5" /> Koneksi Printer
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Jenis Printer</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 'thermal', label: 'Thermal', icon: Printer },
                  { value: 'inkjet', label: 'Inkjet', icon: Printer },
                  { value: 'laser', label: 'Laser', icon: Printer }
                ].map(type => (
                  <button
                    key={type.value}
                    onClick={() => setSettings(s => ({ ...s, printer_type: type.value }))}
                    className={`p-3 rounded-lg border flex flex-col items-center gap-2 transition-colors ${
                      settings.printer_type === type.value 
                        ? 'border-amber-500 bg-amber-500/10 text-amber-400' 
                        : 'border-red-900/30 hover:border-red-700/50'
                    }`}
                  >
                    <type.icon className="h-5 w-5" />
                    <span className="text-sm">{type.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Metode Koneksi</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 'usb', label: 'USB', icon: Usb },
                  { value: 'bluetooth', label: 'Bluetooth', icon: Bluetooth },
                  { value: 'network', label: 'Network', icon: Wifi }
                ].map(conn => (
                  <button
                    key={conn.value}
                    onClick={() => setSettings(s => ({ ...s, connection_type: conn.value }))}
                    className={`p-3 rounded-lg border flex flex-col items-center gap-2 transition-colors ${
                      settings.connection_type === conn.value 
                        ? 'border-amber-500 bg-amber-500/10 text-amber-400' 
                        : 'border-red-900/30 hover:border-red-700/50'
                    }`}
                  >
                    <conn.icon className="h-5 w-5" />
                    <span className="text-sm">{conn.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {settings.connection_type === 'usb' && (
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama Printer</label>
                <input
                  type="text"
                  value={settings.printer_name}
                  onChange={(e) => setSettings(s => ({ ...s, printer_name: e.target.value }))}
                  placeholder="Nama printer USB..."
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                />
              </div>
            )}

            {settings.connection_type === 'network' && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">IP Address</label>
                  <input
                    type="text"
                    value={settings.ip_address}
                    onChange={(e) => setSettings(s => ({ ...s, ip_address: e.target.value }))}
                    placeholder="192.168.1.100"
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Port</label>
                  <input
                    type="number"
                    value={settings.port}
                    onChange={(e) => setSettings(s => ({ ...s, port: Number(e.target.value) }))}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
              </div>
            )}

            {settings.connection_type === 'bluetooth' && (
              <div>
                <label className="block text-sm text-gray-400 mb-1">Bluetooth Address</label>
                <input
                  type="text"
                  value={settings.bluetooth_address}
                  onChange={(e) => setSettings(s => ({ ...s, bluetooth_address: e.target.value }))}
                  placeholder="00:11:22:33:44:55"
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                />
              </div>
            )}

            <div>
              <label className="block text-sm text-gray-400 mb-2">Lebar Kertas</label>
              <div className="flex gap-2">
                {[58, 80].map(width => (
                  <button
                    key={width}
                    onClick={() => setSettings(s => ({ ...s, paper_width: width }))}
                    className={`px-4 py-2 rounded-lg border ${
                      settings.paper_width === width 
                        ? 'border-amber-500 bg-amber-500/10 text-amber-400' 
                        : 'border-red-900/30'
                    }`}
                  >
                    {width}mm
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.auto_cut}
                  onChange={(e) => setSettings(s => ({ ...s, auto_cut: e.target.checked }))}
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-300">Auto Cut</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.open_drawer}
                  onChange={(e) => setSettings(s => ({ ...s, open_drawer: e.target.checked }))}
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-300">Buka Laci Kas</span>
              </label>
            </div>
          </div>
        </div>

        {/* Receipt Layout */}
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-amber-200 mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5" /> Tampilan Struk
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Header - Nama Toko</label>
              <input
                type="text"
                value={settings.header_text}
                onChange={(e) => setSettings(s => ({ ...s, header_text: e.target.value }))}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Header - Subtitle</label>
              <input
                type="text"
                value={settings.header_subtitle}
                onChange={(e) => setSettings(s => ({ ...s, header_subtitle: e.target.value }))}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Alamat</label>
              <textarea
                value={settings.header_address}
                onChange={(e) => setSettings(s => ({ ...s, header_address: e.target.value }))}
                rows={2}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Telepon</label>
              <input
                type="text"
                value={settings.header_phone}
                onChange={(e) => setSettings(s => ({ ...s, header_phone: e.target.value }))}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
              />
            </div>

            <div className="border-t border-red-900/30 pt-4">
              <label className="block text-sm text-gray-400 mb-1">Footer - Pesan</label>
              <input
                type="text"
                value={settings.footer_text}
                onChange={(e) => setSettings(s => ({ ...s, footer_text: e.target.value }))}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Footer - Catatan</label>
              <input
                type="text"
                value={settings.footer_note}
                onChange={(e) => setSettings(s => ({ ...s, footer_note: e.target.value }))}
                placeholder="Barang yang sudah dibeli tidak dapat ditukar/dikembalikan"
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
              />
            </div>

            <div className="flex items-center gap-4 flex-wrap">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.show_logo}
                  onChange={(e) => setSettings(s => ({ ...s, show_logo: e.target.checked }))}
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-300">Tampilkan Logo</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.show_barcode}
                  onChange={(e) => setSettings(s => ({ ...s, show_barcode: e.target.checked }))}
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-300">Tampilkan Barcode</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.show_qr_code}
                  onChange={(e) => setSettings(s => ({ ...s, show_qr_code: e.target.checked }))}
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-300">Tampilkan QR Code</span>
              </label>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Ukuran Font</label>
              <div className="flex gap-2">
                {['small', 'normal', 'large'].map(size => (
                  <button
                    key={size}
                    onClick={() => setSettings(s => ({ ...s, font_size: size }))}
                    className={`px-4 py-2 rounded-lg border capitalize ${
                      settings.font_size === size 
                        ? 'border-amber-500 bg-amber-500/10 text-amber-400' 
                        : 'border-red-900/30'
                    }`}
                  >
                    {size === 'small' ? 'Kecil' : size === 'normal' ? 'Normal' : 'Besar'}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Jumlah Copy</label>
              <input
                type="number"
                min="1"
                max="5"
                value={settings.print_copies}
                onChange={(e) => setSettings(s => ({ ...s, print_copies: Number(e.target.value) }))}
                className="w-24 px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Receipt Preview */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-amber-200 mb-4 flex items-center gap-2">
          <Monitor className="h-5 w-5" /> Preview Struk
        </h2>
        
        <div className="flex justify-center">
          <div className="bg-white text-black p-4 rounded-lg shadow-lg" style={{ width: settings.paper_width === 58 ? '220px' : '300px', fontFamily: 'monospace' }}>
            <div className="text-center border-b border-dashed border-gray-400 pb-2 mb-2">
              {settings.show_logo && (
                <div className="text-2xl font-bold mb-1">🏪</div>
              )}
              <div className={`font-bold ${settings.font_size === 'small' ? 'text-sm' : settings.font_size === 'large' ? 'text-lg' : 'text-base'}`}>
                {settings.header_text || 'NAMA TOKO'}
              </div>
              {settings.header_subtitle && (
                <div className="text-xs text-gray-600">{settings.header_subtitle}</div>
              )}
              {settings.header_address && (
                <div className="text-xs text-gray-600 mt-1">{settings.header_address}</div>
              )}
              {settings.header_phone && (
                <div className="text-xs text-gray-600">Telp: {settings.header_phone}</div>
              )}
            </div>
            
            <div className="text-xs mb-2">
              <div>No: TRX-001</div>
              <div>Tgl: {new Date().toLocaleString('id-ID')}</div>
              <div>Kasir: Administrator</div>
            </div>
            
            <div className="border-t border-dashed border-gray-400 py-2">
              <div className="flex justify-between text-xs">
                <span>Produk Test</span>
                <span>Rp 25.000</span>
              </div>
              <div className="text-xs text-gray-500 pl-2">2 x Rp 12.500</div>
            </div>
            
            <div className="border-t border-dashed border-gray-400 pt-2">
              <div className="flex justify-between text-sm font-bold">
                <span>TOTAL</span>
                <span>Rp 25.000</span>
              </div>
              <div className="flex justify-between text-xs">
                <span>Tunai</span>
                <span>Rp 30.000</span>
              </div>
              <div className="flex justify-between text-xs">
                <span>Kembali</span>
                <span>Rp 5.000</span>
              </div>
            </div>
            
            <div className="text-center border-t border-dashed border-gray-400 mt-2 pt-2">
              <div className="text-xs text-gray-600">{settings.footer_text}</div>
              {settings.footer_note && (
                <div className="text-xs text-gray-500 mt-1">{settings.footer_note}</div>
              )}
              {settings.show_barcode && (
                <div className="mt-2 text-xs">||||| ||| |||| |||</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrinterSettings;
