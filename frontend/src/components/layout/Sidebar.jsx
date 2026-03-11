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
  Globe, Plus, List, ChevronsRight, Send, Table, QrCode, Calendar, Award, Grid,
  RefreshCcw
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { usePermission } from '../../contexts/PermissionContext';

const Sidebar = ({ isOpen, setIsOpen }) => {
  const { user, logout } = useAuth();
  const { hasPermission, canSeeMenu, permissions } = usePermission();
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

  // ============================================================
  // STRUKTUR MENU PERSIS SEPERTI iPOS ULTIMATE
  // ============================================================
  const menuStructure = [
    // Dashboard
    { 
      name: 'Dashboard', 
      icon: LayoutDashboard, 
      path: '/dashboard',
      roles: ['owner', 'admin', 'supervisor', 'cashier', 'finance', 'inventory']
    },

    // ============================================================
    // MASTER DATA - iPOS Style (LENGKAP)
    // ============================================================
    {
      name: 'Master Data',
      icon: Database,
      roles: ['owner', 'admin', 'supervisor', 'inventory'],
      submenu: [
        { name: 'Daftar Item', icon: Package, path: '/master/items' },
        { name: 'Item Baru', icon: Plus, path: '/master/items?new=true' },
        { name: 'Datasheet', icon: Table, path: '/master/datasheet' },
        { name: 'Kartu Stok', icon: ClipboardList, path: '/master/stock-cards' },
        { name: 'Barcode', icon: QrCode, path: '/master/barcode' },
        { divider: true, label: 'Promosi & Diskon' },
        { name: 'Diskon Periode', icon: Percent, path: '/master/discounts' },
        { name: 'Periode Promosi', icon: Calendar, path: '/master/promotions' },
        { divider: true, label: 'Partner' },
        { name: 'Daftar Supplier', icon: Truck, path: '/master/suppliers' },
        { name: 'Daftar Pelanggan', icon: Users, path: '/master/customers' },
        { name: 'Daftar Sales', icon: UserCheck, path: '/master/sales-persons' },
        { name: 'Grup Pelanggan', icon: UserCog, path: '/master/customer-groups' },
        { name: 'Point Pelanggan', icon: Star, path: '/master/customer-points' },
        { divider: true, label: 'Referensi' },
        { name: 'Wilayah', icon: Globe, path: '/master/regions' },
        { name: 'Satuan', icon: Scale, path: '/master/units' },
        { name: 'Dept/Gudang', icon: Warehouse, path: '/master/warehouses' },
        { name: 'E-Money', icon: CreditCard, path: '/master/emoney' },
        { name: 'Jenis Barang', icon: Tags, path: '/master/item-types' },
        { name: 'Merk', icon: Award, path: '/master/brands' },
        { name: 'Kategori', icon: Grid, path: '/master/categories' },
        { name: 'Bank', icon: Building2, path: '/master/banks' },
        { name: 'Ongkir', icon: MapPin, path: '/master/shipping-costs' },
        { divider: true, label: 'Sistem' },
        { name: 'Cabang', icon: Building, path: '/settings/branches' },
        { name: 'User', icon: UserCog, path: '/settings/users' },
        { name: 'Setting Akun ERP', icon: Settings, path: '/master/setting-akun' },
        { name: 'ERP Hardening', icon: Shield, path: '/master/erp-hardening' },
      ]
    },

    // ============================================================
    // PENJUALAN - iPOS Style (FULL)
    // ============================================================
    {
      name: 'Penjualan',
      icon: ShoppingBag,
      roles: ['owner', 'admin', 'supervisor', 'cashier'],
      submenu: [
        { name: 'Pesanan Jual List', icon: List, path: '/sales/orders' },
        { name: 'Tambah Pesanan Penjualan', icon: Plus, path: '/sales/orders/add' },
        { divider: true },
        { name: 'Daftar Penjualan', icon: FileText, path: '/sales/list' },
        { name: 'Tambah Penjualan', icon: Plus, path: '/sales/add' },
        { divider: true },
        { name: 'Daftar Kasir', icon: ShoppingCart, path: '/sales/cashier-list' },
        { name: 'Tambah Kasir', icon: Plus, path: '/kasir' },
        { divider: true },
        { name: 'History Harga Jual', icon: History, path: '/sales/price-history' },
        { divider: true },
        { name: 'Daftar Tukar Tambah', icon: ArrowLeftRight, path: '/sales/trade-in' },
        { name: 'Tambah Tukar Tambah', icon: Plus, path: '/sales/trade-in/add' },
        { divider: true },
        { name: 'Daftar Pembayaran Piutang', icon: Wallet, path: '/sales/ar-payments' },
        { name: 'Tambah Pembayaran Piutang', icon: Plus, path: '/sales/ar-payments/add' },
        { divider: true },
        { name: 'Daftar Retur Penjualan', icon: RotateCcw, path: '/sales/returns' },
        { name: 'Tambah Retur Penjualan', icon: Plus, path: '/sales/returns/add' },
        { divider: true },
        { name: 'Point Transaksi', icon: Star, path: '/sales/points' },
        { divider: true },
        { name: 'Daftar Pembayaran Komisi Sales', icon: BadgeDollarSign, path: '/sales/commission-payments' },
        { name: 'Tambah Pembayaran Komisi Sales', icon: Plus, path: '/sales/commission-payments/add' },
        { divider: true },
        { name: 'Daftar Pengiriman', icon: Send, path: '/sales/deliveries' },
        { divider: true },
        { name: 'Laporan CSV/XML Faktur Pajak', icon: FileSpreadsheet, path: '/sales/tax-export' },
      ]
    },

    // ============================================================
    // PEMBELIAN - iPOS Style
    // ============================================================
    {
      name: 'Pembelian',
      icon: Truck,
      roles: ['owner', 'admin', 'supervisor', 'inventory'],
      submenu: [
        { name: 'Pesanan Pembelian', icon: List, path: '/purchase/orders' },
        { name: 'Tambah Pesanan Pembelian', icon: Plus, path: '/purchase/orders/add' },
        { divider: true },
        { name: 'Daftar Pembelian', icon: FileText, path: '/purchase/list' },
        { name: 'Tambah Pembelian', icon: Plus, path: '/purchase/add' },
        { divider: true },
        { name: 'History Harga Beli', icon: History, path: '/purchase/price-history' },
        { divider: true },
        { name: 'Daftar Pembayaran Hutang', icon: Wallet, path: '/purchase/ap-payments' },
        { name: 'Tambah Pembayaran Hutang', icon: Plus, path: '/purchase/ap-payments/add' },
        { divider: true },
        { name: 'Daftar Retur Pembelian', icon: RotateCcw, path: '/purchase/returns' },
        { name: 'Tambah Retur Pembelian', icon: Plus, path: '/purchase/returns/add' },
      ]
    },

    // ============================================================
    // INVENTORY / PERSEDIAAN - iPOS Style
    // ============================================================
    {
      name: 'Inventory',
      icon: Boxes,
      roles: ['owner', 'admin', 'supervisor', 'inventory'],
      submenu: [
        { name: 'Stok Barang', icon: Package, path: '/inventory/stock-list' },
        { name: 'Kartu Stok', icon: ClipboardList, path: '/inventory/kartu-stok' },
        { name: 'Mutasi Gudang', icon: History, path: '/inventory/mutations' },
        { name: 'Transfer Gudang', icon: ArrowLeftRight, path: '/inventory/transfer' },
        { name: 'Stock Opname', icon: ClipboardList, path: '/inventory/opname' },
        { name: 'Penyesuaian Stok', icon: Settings, path: '/inventory/adjustment' },
      ]
    },

    // ============================================================
    // AKUNTANSI - iPOS Style
    // ============================================================
    {
      name: 'Akuntansi',
      icon: Calculator,
      roles: ['owner', 'admin', 'finance'],
      submenu: [
        { name: 'Chart Of Accounts', icon: BookOpen, path: '/accounting/coa' },
        { name: 'Jurnal Umum', icon: FileText, path: '/accounting/journals' },
        { name: 'Buku Besar', icon: BookOpen, path: '/accounting/ledger' },
        { name: 'Neraca Saldo', icon: Scale, path: '/accounting/trial-balance' },
        { name: 'Neraca', icon: BookOpen, path: '/accounting/balance-sheet' },
        { name: 'Laba Rugi', icon: BarChart2, path: '/accounting/income-statement' },
        { divider: true, label: 'Financial Control' },
        { name: 'Multi Tax Engine', icon: Percent, path: '/accounting/financial-control' },
        { name: 'Consistency Checker', icon: AlertCircle, path: '/accounting/financial-control' },
      ]
    },

    // ============================================================
    // HUTANG (AP) - iPOS Style
    // ============================================================
    {
      name: 'Hutang',
      icon: Wallet,
      roles: ['owner', 'admin', 'finance'],
      submenu: [
        { name: 'Daftar Hutang', icon: List, path: '/hutang/list' },
        { name: 'Pembayaran Hutang', icon: CreditCard, path: '/hutang/payments' },
        { name: 'Umur Hutang', icon: Clock, path: '/hutang/aging' },
      ]
    },

    // ============================================================
    // PIUTANG (AR) - iPOS Style
    // ============================================================
    {
      name: 'Piutang',
      icon: CreditCard,
      roles: ['owner', 'admin', 'finance'],
      submenu: [
        { name: 'Daftar Piutang', icon: List, path: '/piutang/list' },
        { name: 'Pembayaran Piutang', icon: Wallet, path: '/piutang/payments' },
        { name: 'Umur Piutang', icon: Clock, path: '/piutang/aging' },
      ]
    },

    // ============================================================
    // KAS / BANK - iPOS Style
    // ============================================================
    {
      name: 'Kas / Bank',
      icon: Banknote,
      roles: ['owner', 'admin', 'finance', 'cashier'],
      submenu: [
        { name: 'Kas Masuk', icon: Download, path: '/kas/in' },
        { name: 'Kas Keluar', icon: Upload, path: '/kas/out' },
        { name: 'Mutasi Kas', icon: ArrowLeftRight, path: '/kas/mutations' },
      ]
    },

    // ============================================================
    // LAPORAN - iPOS Style
    // ============================================================
    {
      name: 'Laporan',
      icon: BarChart3,
      roles: ['owner', 'admin', 'supervisor', 'finance'],
      submenu: [
        { name: 'Laporan Penjualan', icon: TrendingUp, path: '/reports/sales' },
        { name: 'Laporan Pembelian', icon: Truck, path: '/reports/purchase' },
        { name: 'Laporan Stok', icon: Boxes, path: '/reports/inventory' },
        { name: 'Laporan Hutang', icon: Wallet, path: '/reports/payables' },
        { name: 'Laporan Piutang', icon: CreditCard, path: '/reports/receivables' },
        { name: 'Laporan Laba Rugi', icon: BarChart2, path: '/reports/profit-loss' },
        { name: 'Laporan Neraca', icon: BookOpen, path: '/reports/balance-sheet' },
        { name: 'Laporan Kartu Stok', icon: ClipboardList, path: '/reports/stock-card' },
      ]
    },

    // ============================================================
    // HR & PAYROLL
    // ============================================================
    {
      name: 'HR & Payroll',
      icon: UserPlus,
      roles: ['owner', 'admin', 'supervisor'],
      submenu: [
        { name: 'Data Karyawan', icon: Users, path: '/employees' },
        { name: 'Absensi', icon: Fingerprint, path: '/absensi' },
        { name: 'Payroll', icon: BadgeDollarSign, path: '/payroll' },
        { name: 'Master Shift', icon: Clock, path: '/master/shifts' },
        { name: 'Master Jabatan', icon: Briefcase, path: '/master/jabatan' },
      ]
    },

    // ============================================================
    // APPROVAL CENTER - Phase 3
    // ============================================================
    {
      name: 'Approval Center',
      icon: FileCheck,
      path: '/approval-center',
      roles: ['owner', 'admin', 'supervisor', 'finance']
    },

    // ============================================================
    // CREDIT CONTROL - Phase 3
    // ============================================================
    {
      name: 'Credit Control',
      icon: CreditCard,
      path: '/credit-control',
      roles: ['owner', 'admin', 'finance']
    },

    // ============================================================
    // STOCK REORDER - Phase 3
    // ============================================================
    {
      name: 'Stock Reorder',
      icon: RefreshCcw,
      path: '/stock-reorder',
      roles: ['owner', 'admin', 'purchasing', 'inventory']
    },

    // ============================================================
    // WAREHOUSE CONTROL - Phase 3
    // ============================================================
    {
      name: 'Warehouse Control',
      icon: Warehouse,
      path: '/warehouse-control',
      roles: ['owner', 'admin', 'inventory']
    },

    // ============================================================
    // PURCHASE PLANNING - Phase 3
    // ============================================================
    {
      name: 'Purchase Planning',
      icon: ClipboardList,
      path: '/purchase-planning',
      roles: ['owner', 'admin', 'purchasing']
    },

    // ============================================================
    // SALES TARGET - Phase 3
    // ============================================================
    {
      name: 'Sales Target',
      icon: Target,
      path: '/sales-target',
      roles: ['owner', 'admin', 'sales_manager']
    },

    // ============================================================
    // PENGATURAN
    // ============================================================
    {
      name: 'Pengaturan',
      icon: Settings,
      roles: ['owner', 'admin'],
      submenu: [
        { name: 'Data User', icon: UserCog, path: '/settings/users' },
        { name: 'Hak Akses', icon: Shield, path: '/settings/roles' },
        { name: 'Data Perusahaan', icon: Building2, path: '/settings/company' },
        { name: 'Cabang', icon: Building2, path: '/settings/branches' },
        { divider: true },
        { name: 'Printer & Struk', icon: Printer, path: '/settings/printer' },
        { name: 'Import Excel', icon: Upload, path: '/settings/import' },
        { name: 'Export Excel', icon: Download, path: '/settings/export' },
        { divider: true },
        { name: 'Log Aktivitas', icon: Clock, path: '/settings/activity-log' },
        { name: 'Backup & Restore', icon: HardDrive, path: '/settings/backup' },
      ]
    },

    // ============================================================
    // SUPER AI (Fitur tambahan OCB TITAN)
    // ============================================================
    {
      name: 'AI Tools',
      icon: Brain,
      roles: ['owner', 'admin'],
      submenu: [
        { name: 'Owner Dashboard', icon: BarChart2, path: '/owner-dashboard' },
        { name: 'Finance Dashboard', icon: DollarSign, path: '/finance-dashboard' },
        { name: 'CFO Dashboard', icon: Briefcase, path: '/cfo-dashboard' },
        { name: 'ERP Dashboard', icon: Database, path: '/erp-dashboard' },
        { divider: true, label: 'AI Intelligence' },
        { name: 'AI Command Center', icon: Brain, path: '/ai-command-center' },
        { name: 'AI Sales Analytics', icon: TrendingUp, path: '/ai-sales' },
        { name: 'AI Business Insight', icon: Sparkles, path: '/ai-bisnis' },
        { name: 'AI Employee Performance', icon: UserCheck, path: '/ai-performance' },
        { name: 'Hallo OCB AI', icon: MessageSquare, path: '/hallo-ai' },
        { divider: true, label: 'War Room & Monitoring' },
        { name: 'War Room', icon: Activity, path: '/warroom' },
        { name: 'War Room V2', icon: Activity, path: '/war-room-v2' },
        { name: 'AI War Room Super', icon: Shield, path: '/ai-warroom-super' },
        { name: 'War Room Alerts', icon: Bell, path: '/warroom-alerts' },
        { divider: true, label: 'CRM & KPI' },
        { name: 'CRM AI', icon: Users, path: '/crm-ai' },
        { name: 'CRM', icon: Users, path: '/crm' },
        { name: 'KPI Performance', icon: Target, path: '/kpi-performance' },
        { divider: true, label: 'Analytics & Reports' },
        { name: 'Analytics', icon: BarChart3, path: '/analytics' },
      ]
    },
  ];

  // Filter menus based on RBAC permissions
  const filteredMenus = menuStructure.filter(item => {
    if (permissions?.all_permissions) return true;
    const roleAllowed = item.roles?.includes(user?.role || 'cashier');
    if (!roleAllowed) return false;
    
    if (item.name.includes('Master Data')) return canSeeMenu('master');
    if (item.name.includes('Pembelian')) return canSeeMenu('purchase');
    if (item.name.includes('Penjualan')) return canSeeMenu('sales');
    if (item.name.includes('Inventory')) return canSeeMenu('inventory');
    if (item.name.includes('Akuntansi')) return canSeeMenu('accounting');
    if (item.name.includes('Laporan')) return canSeeMenu('report');
    if (item.name.includes('Pengaturan')) return canSeeMenu('setting');
    
    return roleAllowed;
  });

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
              : 'text-gray-400 hover:bg-red-900/10 hover:text-red-200 border border-transparent'
          }`
        }
      >
        <item.icon className="h-5 w-5" />
        <span className="font-medium">{item.name}</span>
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
            <p className="text-[10px] text-red-300/50 mt-0.5">Enterprise Retail System - iPOS Style</p>
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
