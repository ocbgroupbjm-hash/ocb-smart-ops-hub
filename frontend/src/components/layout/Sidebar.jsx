import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, ShoppingCart, Package, Boxes, Users, Building2, 
  Settings, LogOut, DollarSign, Truck, UserCog, Warehouse, FileText,
  BarChart3, Calculator, Brain, Shield, Sparkles, ChevronDown, ChevronRight,
  Database, Tags, Percent, Gift, MapPin, CreditCard, Building, Scale,
  ClipboardList, Receipt, History, RotateCcw, TrendingUp, Printer,
  FileSpreadsheet, HardDrive, BookOpen, Wallet, ArrowLeftRight, 
  PiggyBank, FileCheck, Archive, Clock, AlertCircle, HelpCircle, Info,
  Upload, Download, Layers, BarChart2, ShoppingBag, UserCheck, Star,
  Activity, Bot, MessageSquare, Target, Megaphone, Banknote, UserPlus,
  CalendarCheck, Briefcase, BadgeDollarSign, Bell, Eye, Fingerprint, FileBarChart,
  Globe
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const Sidebar = ({ isOpen, setIsOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [expandedMenus, setExpandedMenus] = useState({});

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleMenu = (menuName) => {
    setExpandedMenus(prev => ({
      ...prev,
      [menuName]: !prev[menuName]
    }));
  };

  // Menu structure like iPOS
  const menuStructure = [
    { 
      name: 'Dashboard', 
      icon: LayoutDashboard, 
      path: '/dashboard', 
      roles: ['owner', 'admin', 'supervisor', 'cashier', 'finance', 'inventory'] 
    },
    {
      name: '🚀 SUPER AI',
      icon: Activity,
      roles: ['owner', 'admin', 'supervisor'],
      highlight: true,
      submenu: [
        { name: '🏢 Warroom', icon: Activity, path: '/warroom', description: 'Monitor seluruh cabang' },
        { name: '⚔️ War Room V2', icon: Eye, path: '/war-room-v2', description: 'Command Center Owner' },
        { name: '🤖 AI Sales', icon: Bot, path: '/ai-sales', description: 'Penjualan otomatis' },
        { name: '💬 Hallo OCB AI', icon: MessageSquare, path: '/hallo-ai' },
        { name: '📊 AI Bisnis', icon: Brain, path: '/ai-bisnis' },
      ]
    },
    {
      name: '🌍 OCB TITAN AI',
      icon: Eye,
      roles: ['owner', 'admin'],
      highlight: true,
      submenu: [
        { name: '🗺️ Global Map', icon: MapPin, path: '/global-map', description: 'Monitor cabang real-time' },
        { name: '🧠 AI Command Center', icon: Brain, path: '/ai-command-center', description: 'Analisis AI' },
        { name: '🚨 War Room Alerts', icon: Bell, path: '/warroom-alerts', description: 'Alert real-time' },
        { name: '🏆 KPI & Performance', icon: Target, path: '/kpi-performance', description: 'Ranking karyawan' },
        { name: '🤖 CRM AI', icon: Bot, path: '/crm-ai', description: 'AI untuk CRM' },
        { name: '📤 Advanced Export', icon: Download, path: '/advanced-export', description: 'Export Excel/PDF' },
        { name: '📥 Import Data', icon: Upload, path: '/import-system', description: 'Import Excel/CSV' },
        { name: '📱 WhatsApp Alerts', icon: Bell, path: '/whatsapp-alerts', description: 'Notifikasi WA' },
      ]
    },
    {
      name: '💼 AI CFO & War Room',
      icon: Shield,
      roles: ['owner', 'admin'],
      highlight: true,
      submenu: [
        { name: '💰 CFO Dashboard', icon: DollarSign, path: '/cfo-dashboard', description: 'Analisis Keuangan AI' },
        { name: '🛡️ AI Super War Room', icon: Shield, path: '/ai-warroom-super', description: 'Prediksi & Fraud Detection' },
      ]
    },
    {
      name: '💰 Operasional',
      icon: Banknote,
      roles: ['owner', 'admin', 'supervisor', 'cashier'],
      highlight: true,
      submenu: [
        { name: 'Setoran Harian', icon: Banknote, path: '/setoran-harian', description: 'Input setoran cabang' },
        { name: 'Selisih Kas', icon: AlertCircle, path: '/selisih-kas', description: 'Plus/Minus tracking' },
        { name: 'Dashboard ERP', icon: BarChart2, path: '/erp-dashboard', description: 'Summary operasional' },
        { name: 'Laporan ERP', icon: FileText, path: '/erp-reports', description: 'Comprehensive reports' },
      ]
    },
    {
      name: '👥 HR & Payroll',
      icon: UserPlus,
      roles: ['owner', 'admin', 'supervisor'],
      submenu: [
        { name: 'Data Karyawan', icon: Users, path: '/employees', description: 'Master karyawan' },
        { name: 'HR Management', icon: Building2, path: '/hr-management', description: 'Training & Struktur' },
        { name: 'Absensi', icon: Fingerprint, path: '/absensi', description: 'Check-in/out GPS' },
        { name: 'Payroll', icon: BadgeDollarSign, path: '/payroll', description: 'Penggajian' },
        { name: '🤖 AI Performance', icon: Target, path: '/ai-performance', description: 'Analisis performa AI' },
        { name: '💰 Payroll Otomatis', icon: Calculator, path: '/payroll-auto', description: 'Gaji otomatis dari absensi' },
        { divider: true },
        { name: 'Master Shift', icon: Clock, path: '/master/shifts' },
        { name: 'Master Jabatan', icon: Briefcase, path: '/master/jabatan' },
        { name: 'Lokasi Absensi', icon: MapPin, path: '/master/lokasi-absensi' },
        { name: 'Aturan Payroll', icon: Settings, path: '/master/payroll-rules' },
      ]
    },
    {
      name: 'Kasir (POS)',
      icon: ShoppingCart,
      path: '/kasir',
      roles: ['owner', 'admin', 'supervisor', 'cashier']
    },
    {
      name: 'Master Data',
      icon: Database,
      roles: ['owner', 'admin', 'supervisor', 'inventory'],
      submenu: [
        { name: 'Daftar Item', icon: Package, path: '/master/items' },
        { name: 'Kategori Item', icon: Tags, path: '/master/categories' },
        { name: 'Satuan', icon: Scale, path: '/master/units' },
        { name: 'Merk', icon: Star, path: '/master/brands' },
        { name: 'Dept/Gudang', icon: Building, path: '/master/warehouses' },
        { name: 'Kartu Stok', icon: ClipboardList, path: '/master/stock-cards' },
        { name: 'Diskon Periode', icon: Percent, path: '/master/discounts' },
        { name: 'Promosi', icon: Gift, path: '/master/promotions' },
        { divider: true },
        { name: 'Daftar Supplier', icon: Truck, path: '/master/suppliers' },
        { name: 'Daftar Pelanggan', icon: Users, path: '/master/customers' },
        { name: 'Daftar Sales', icon: UserCheck, path: '/master/sales-persons' },
        { name: 'Grup Pelanggan', icon: Users, path: '/master/customer-groups' },
        { name: 'Point Pelanggan', icon: Star, path: '/master/customer-points' },
        { name: 'Wilayah', icon: MapPin, path: '/master/regions' },
        { divider: true },
        { name: 'E-Money', icon: CreditCard, path: '/master/emoney' },
        { name: 'Bank', icon: Building2, path: '/master/banks' },
        { name: 'Ongkir', icon: Truck, path: '/master/shipping-costs' },
      ]
    },
    {
      name: 'Pembelian',
      icon: Truck,
      roles: ['owner', 'admin', 'supervisor', 'inventory'],
      submenu: [
        { name: 'Pesanan Pembelian', icon: ClipboardList, path: '/purchase/orders' },
        { name: 'Daftar Pembelian', icon: FileText, path: '/purchase/list' },
        { name: 'Penerimaan Barang', icon: Package, path: '/purchase/receiving' },
        { name: 'History Harga Beli', icon: History, path: '/purchase/price-history' },
        { name: 'Daftar Pembayaran', icon: Wallet, path: '/purchase/payments' },
        { name: 'Status Lunas', icon: FileCheck, path: '/purchase/payment-status' },
        { name: 'Retur Pembelian', icon: RotateCcw, path: '/purchase/returns' },
      ]
    },
    {
      name: 'Penjualan',
      icon: ShoppingBag,
      roles: ['owner', 'admin', 'supervisor', 'cashier'],
      submenu: [
        { name: 'Pesanan Penjualan', icon: ClipboardList, path: '/sales/orders' },
        { name: 'Daftar Penjualan', icon: FileText, path: '/sales/list' },
        { name: 'Penjualan Kasir', icon: ShoppingCart, path: '/sales/cashier-sales' },
        { name: 'History Harga Jual', icon: History, path: '/sales/price-history' },
        { name: 'Tukar Tambah', icon: ArrowLeftRight, path: '/sales/trade-in' },
        { divider: true },
        { name: 'Daftar Pembayaran', icon: Wallet, path: '/sales/payments' },
        { name: 'Status Lunas', icon: FileCheck, path: '/sales/payment-status' },
        { divider: true },
        { name: 'Retur Penjualan', icon: RotateCcw, path: '/sales/returns' },
        { name: 'Point Penjualan', icon: Star, path: '/sales/points' },
        { name: 'Data Pengiriman', icon: Truck, path: '/sales/deliveries' },
      ]
    },
    {
      name: 'Persediaan',
      icon: Boxes,
      roles: ['owner', 'admin', 'supervisor', 'inventory'],
      submenu: [
        { name: 'Daftar Stok', icon: Package, path: '/inventory/stock-list' },
        { name: 'Kartu Stok', icon: ClipboardList, path: '/inventory/stock-cards' },
        { name: 'Stok Masuk', icon: Download, path: '/inventory/stock-in' },
        { name: 'Stok Keluar', icon: Upload, path: '/inventory/stock-out' },
        { name: 'Transfer Stok', icon: ArrowLeftRight, path: '/inventory/transfer' },
        { name: 'Mutasi Stok', icon: History, path: '/inventory/mutations' },
        { name: 'Stok Opname', icon: ClipboardList, path: '/inventory/opname' },
        { name: 'Serial Number', icon: FileText, path: '/inventory/serial-numbers' },
        { name: 'Rakitan Produk', icon: Layers, path: '/inventory/assemblies' },
      ]
    },
    {
      name: 'Akuntansi',
      icon: Calculator,
      roles: ['owner', 'admin', 'finance'],
      submenu: [
        { name: 'Daftar Perkiraan', icon: BookOpen, path: '/accounting/coa' },
        { divider: true },
        { name: 'Kas Masuk', icon: Download, path: '/accounting/cash-in' },
        { name: 'Kas Keluar', icon: Upload, path: '/accounting/cash-out' },
        { name: 'Kas Transfer', icon: ArrowLeftRight, path: '/accounting/cash-transfer' },
        { divider: true },
        { name: 'Deposit Pelanggan', icon: PiggyBank, path: '/accounting/customer-deposit' },
        { name: 'Deposit Supplier', icon: PiggyBank, path: '/accounting/supplier-deposit' },
        { divider: true },
        { name: 'Daftar Jurnal', icon: FileText, path: '/accounting/journals' },
        { name: 'Buku Besar', icon: BookOpen, path: '/accounting/ledger' },
        { divider: true },
        { name: 'Saldo Awal', icon: Wallet, path: '/accounting/opening-balance' },
        { name: 'Tutup Tahun', icon: Archive, path: '/accounting/year-end' },
        { name: 'Setting Perkiraan', icon: Settings, path: '/accounting/coa-settings' },
      ]
    },
    {
      name: 'Laporan',
      icon: BarChart3,
      roles: ['owner', 'admin', 'supervisor', 'finance'],
      submenu: [
        { name: 'Lap. Penjualan', icon: TrendingUp, path: '/reports/sales' },
        { name: 'Lap. Pembelian', icon: Truck, path: '/reports/purchase' },
        { name: 'Lap. Persediaan', icon: Boxes, path: '/reports/inventory' },
        { name: 'Lap. Produk Terlaris', icon: Star, path: '/reports/best-sellers' },
        { divider: true },
        { name: 'Lap. Hutang', icon: FileText, path: '/reports/payables' },
        { name: 'Lap. Piutang', icon: FileText, path: '/reports/receivables' },
        { name: 'Lap. Kas', icon: Wallet, path: '/reports/cash' },
        { divider: true },
        { name: 'Neraca Saldo', icon: Scale, path: '/accounting/trial-balance' },
        { name: 'Neraca', icon: BookOpen, path: '/accounting/balance-sheet' },
        { name: 'Lap. Laba Rugi', icon: BarChart2, path: '/accounting/income-statement' },
        { name: 'Lap. Arus Kas', icon: ArrowLeftRight, path: '/accounting/cash-flow' },
        { divider: true },
        { name: 'Lap. Cabang', icon: Building2, path: '/reports/branches' },
        { name: 'Lap. Kasir', icon: UserCheck, path: '/reports/cashiers' },
        { name: 'Lap. Supplier', icon: Truck, path: '/reports/suppliers' },
        { name: 'Lap. Pelanggan', icon: Users, path: '/reports/customers' },
      ]
    },
    {
      name: 'Pengaturan',
      icon: Settings,
      roles: ['owner', 'admin'],
      submenu: [
        { name: 'Data User', icon: UserCog, path: '/settings/users' },
        { name: 'Hak Akses', icon: Shield, path: '/settings/roles' },
        { name: 'Data Perusahaan', icon: Building2, path: '/settings/company' },
        { name: 'Pengaturan Umum', icon: Settings, path: '/settings/general' },
        { divider: true },
        { name: 'Cabang', icon: Building2, path: '/settings/branches' },
        { name: 'Periode Transaksi', icon: Clock, path: '/settings/periods' },
        { name: 'Setting Nomor', icon: FileText, path: '/settings/numbering' },
        { divider: true },
        { name: 'Printer & Struk', icon: Printer, path: '/settings/printer' },
        { name: 'Tema', icon: Layers, path: '/settings/theme' },
        { divider: true },
        { name: 'Import Excel', icon: Upload, path: '/settings/import' },
        { name: 'Export Excel', icon: Download, path: '/settings/export' },
        { name: 'Backup & Restore', icon: HardDrive, path: '/settings/backup' },
        { name: 'Kelola Bisnis', icon: Building2, path: '/kelola-bisnis' },
        { divider: true },
        { name: 'Log Aktivitas', icon: Clock, path: '/settings/activity-log' },
        { name: 'Analisa Sistem', icon: AlertCircle, path: '/settings/system-analysis' },
        { name: 'Panduan', icon: HelpCircle, path: '/settings/help' },
        { name: 'Informasi', icon: Info, path: '/settings/info' },
      ]
    },
  ];

  const filteredMenus = menuStructure.filter(item => 
    item.roles?.includes(user?.role || 'cashier')
  );

  const roleLabels = {
    owner: 'Pemilik',
    admin: 'Administrator',
    supervisor: 'Supervisor',
    cashier: 'Kasir',
    finance: 'Keuangan',
    inventory: 'Gudang'
  };

  const renderMenuItem = (item, index) => {
    if (item.submenu) {
      const isExpanded = expandedMenus[item.name];
      return (
        <div key={item.name}>
          <button
            onClick={() => toggleMenu(item.name)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-400 hover:bg-red-900/10 hover:text-red-200 border border-transparent transition-all duration-200"
          >
            <item.icon className="h-5 w-5" />
            <span className="font-medium flex-1 text-left">{item.name}</span>
            {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
          {isExpanded && (
            <div className="ml-4 mt-1 space-y-0.5 border-l border-red-900/20 pl-2">
              {item.submenu.map((subItem, subIndex) => {
                if (subItem.divider) {
                  return <div key={`divider-${subIndex}`} className="border-t border-red-900/20 my-2" />;
                }
                return (
                  <NavLink
                    key={subItem.path}
                    to={subItem.path}
                    onClick={() => setIsOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all duration-200 ${
                        isActive
                          ? 'bg-gradient-to-r from-red-900/40 to-amber-900/20 text-amber-200 border border-red-700/30'
                          : 'text-gray-400 hover:bg-red-900/10 hover:text-red-200'
                      }`
                    }
                  >
                    <subItem.icon className="h-4 w-4" />
                    <span>{subItem.name}</span>
                  </NavLink>
                );
              })}
            </div>
          )}
        </div>
      );
    }

    return (
      <NavLink
        key={item.path}
        to={item.path}
        onClick={() => setIsOpen(false)}
        data-testid={`nav-${item.name.toLowerCase().replace(/\s/g, '-')}`}
        className={({ isActive }) =>
          `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
            isActive
              ? 'bg-gradient-to-r from-red-900/40 to-amber-900/20 text-amber-200 border border-red-700/30 shadow-lg shadow-red-900/20'
              : item.highlight
                ? 'text-purple-300 hover:bg-purple-900/20 hover:text-purple-200 border border-purple-700/20'
                : 'text-gray-400 hover:bg-red-900/10 hover:text-red-200 border border-transparent'
          }`
        }
      >
        <item.icon className={`h-5 w-5 ${item.highlight ? 'text-purple-400' : ''}`} />
        <span className="font-medium">{item.name}</span>
        {item.highlight && <span className="ml-auto text-[10px] px-1.5 py-0.5 bg-purple-600/30 text-purple-300 rounded">AI</span>}
      </NavLink>
    );
  };

  return (
    <>
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
      
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-72 bg-gradient-to-b from-[#0a0608] to-[#120a0c] border-r border-red-900/20 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-4 border-b border-red-900/20">
            <h1 className="text-xl font-bold bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent">
              OCB AI TITAN
            </h1>
            <p className="text-[10px] text-red-300/50 mt-0.5">Enterprise Retail AI System</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-3 space-y-1">
            {filteredMenus.map((item, index) => renderMenuItem(item, index))}
          </nav>

          {/* User Info & Logout */}
          <div className="p-3 border-t border-red-900/20 bg-red-950/20">
            <div className="flex items-center gap-3 mb-2">
              <div className="h-9 w-9 rounded-full bg-gradient-to-br from-red-600 to-amber-500 flex items-center justify-center text-white font-semibold text-sm shadow-lg shadow-red-900/30">
                {user?.name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-amber-100 truncate">{user?.name}</p>
                <p className="text-[10px] text-red-300/50">{roleLabels[user?.role] || user?.role} • {user?.branch?.code || 'HQ'}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-3 py-1.5 text-sm text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
              data-testid="logout-btn"
            >
              <LogOut className="h-4 w-4" />
              <span>Keluar</span>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
