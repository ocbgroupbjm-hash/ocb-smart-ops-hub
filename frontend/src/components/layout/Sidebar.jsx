import React, { useState, useEffect } from 'react';
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
  RefreshCcw, BanknoteIcon, AlertTriangle, Puzzle, Monitor
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { usePermission } from '../../contexts/PermissionContext';
import { 
  canAccessModule, 
  shouldShowMenu, 
  requiresShiftForTransaction,
  ROLE_PERMISSIONS,
  getKasirAllowedMenus 
} from '../../utils/rbacHelper';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const Sidebar = ({ isOpen, setIsOpen }) => {
  const { user, logout } = useAuth();
  const { hasPermission, canSeeMenu, permissions } = usePermission();
  const navigate = useNavigate();
  const [expandedMenus, setExpandedMenus] = useState({});
  const [shiftStatus, setShiftStatus] = useState({ hasActiveShift: false, shift: null });
  const [showShiftWarning, setShowShiftWarning] = useState(false);

  // Check shift status for kasir
  useEffect(() => {
    const checkKasirShift = async () => {
      const userRole = user?.role?.toLowerCase();
      if (userRole === 'kasir' || userRole === 'cashier') {
        try {
          const token = localStorage.getItem('token');
          const response = await axios.get(`${API_URL}/api/cash-control/shift/check`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setShiftStatus({
            hasActiveShift: response.data.has_active_shift,
            shift: response.data.shift
          });
        } catch (error) {
          console.error('Shift check error:', error);
        }
      }
    };
    checkKasirShift();
  }, [user]);

  const handleLogout = async () => {
    const userRole = user?.role?.toLowerCase();
    
    // GUARD: Kasir tidak boleh logout jika shift masih aktif
    if ((userRole === 'kasir' || userRole === 'cashier') && shiftStatus.hasActiveShift) {
      setShowShiftWarning(true);
      return;
    }
    
    logout();
    navigate('/login');
  };

  const handleCloseShiftAndLogout = () => {
    setShowShiftWarning(false);
    navigate('/cash-control');
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
        { name: 'Data Sheet', icon: Table, path: '/master/datasheet', badge: 'NEW' }, // RESTORED: TASK 2 - 2026-03-15
        // Kartu Stok dipindahkan ke menu Inventory (menghindari duplicate)
        { name: 'Barcode', icon: QrCode, path: '/master/barcode' },
        { divider: true, label: 'Promosi & Diskon' },
        { name: 'Diskon', icon: Percent, path: '/master/discounts' },
        { name: 'Promosi', icon: Calendar, path: '/master/promotions' },
        { divider: true, label: 'Partner' },
        { name: 'Daftar Supplier', icon: Truck, path: '/master/suppliers' },
        { name: 'Pelanggan', icon: Users, path: '/master/customers' },
        { name: 'Daftar Sales', icon: UserCheck, path: '/master/sales-persons' },
        { name: 'Grup Pelanggan', icon: UserCog, path: '/master/customer-groups' },
        { name: 'Point Pelanggan', icon: Star, path: '/master/customer-points' },
        { divider: true, label: 'Referensi' },
        { name: 'Wilayah', icon: Globe, path: '/master/regions' },
        { name: 'Satuan', icon: Scale, path: '/master/units' },
        { name: 'Dept/Gudang', icon: Warehouse, path: '/master/warehouses' },
        { name: 'E-Money', icon: CreditCard, path: '/master/emoney' },
        // HIDDEN: MasterItemTypes - jarang dipakai (Phase A Cleanup 2026-03-13)
        // { name: 'Jenis Barang', icon: Tags, path: '/master/item-types' },
        { name: 'Merk', icon: Award, path: '/master/brands' },
        { name: 'Kategori', icon: Grid, path: '/master/categories' },
        { name: 'Bank', icon: Building2, path: '/master/banks' },
        { name: 'Ongkir', icon: MapPin, path: '/master/shipping-costs' },
        { divider: true, label: 'Sistem' },
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
        { name: 'POS Kasir', icon: Monitor, path: '/pos', highlight: true },
        { divider: true },
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
        // Pembayaran Piutang dipindahkan ke menu Piutang (menghindari duplicate)
        { name: 'Daftar Pengiriman', icon: Send, path: '/sales/deliveries' },
        { divider: true },
        { name: 'Laporan CSV/XML Faktur Pajak', icon: FileSpreadsheet, path: '/sales/tax-export' },
      ]
    },

    // ============================================================
    // PEMBELIAN - iPOS Style (CONSOLIDATED - Blueprint v2.4.6)
    // Separated: A. PO/Procurement, B. Histori Pembelian Aktual
    // ============================================================
    {
      name: 'Pembelian',
      icon: Truck,
      roles: ['owner', 'admin', 'supervisor', 'inventory'],
      submenu: [
        { name: 'Quick Purchase', icon: Monitor, path: '/purchase/quick', highlight: true },
        // A. PO / Procurement
        { divider: true, label: 'PO / Procurement' },
        { name: 'Daftar PO Pembelian', icon: List, path: '/purchase/orders' },
        { name: 'Buat PO Pembelian', icon: Plus, path: '/purchase/orders/add' },
        { name: 'Terima Barang', icon: Package, path: '/purchase/receiving' },
        // B. Histori Pembelian Aktual
        { divider: true, label: 'Histori Pembelian' },
        { name: 'Daftar Pembelian', icon: ClipboardList, path: '/purchase/history' },
        { name: 'History Harga Beli', icon: History, path: '/purchase/price-history' },
        // Retur
        { divider: true, label: 'Retur' },
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
        { name: 'Quick Stock', icon: Package, path: '/inventory/quick', highlight: true },
        { divider: true, label: 'Data Stok' },
        { name: 'Stok Barang', icon: Package, path: '/inventory/stock-list' },
        { name: 'Kartu Stok', icon: ClipboardList, path: '/inventory/kartu-stok' },
        { name: 'Mutasi Gudang', icon: History, path: '/inventory/mutations' },
        { name: 'Transfer Gudang', icon: ArrowLeftRight, path: '/inventory/transfer' },
        { name: 'Stock Opname', icon: ClipboardList, path: '/inventory/opname' },
        { name: 'Penyesuaian Stok', icon: Settings, path: '/inventory/adjustment' },
        { divider: true, label: 'Manufaktur' },
        { name: 'Perakitan Voucher', icon: Puzzle, path: '/inventory/assembly-voucher', badge: 'NEW' },
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
        // HIDDEN: FinancialControl - advanced feature (Phase A Cleanup 2026-03-13)
        // { divider: true, label: 'Financial Control' },
        // { name: 'Multi Tax Engine', icon: Percent, path: '/accounting/financial-control' },
        // { name: 'Consistency Checker', icon: AlertCircle, path: '/accounting/financial-control' },
      ]
    },

    // ============================================================
    // HUTANG (AP) - iPOS Style - PRIMARY MENU untuk Hutang
    // ============================================================
    {
      name: 'Hutang',
      icon: Wallet,
      roles: ['owner', 'admin', 'finance'],
      submenu: [
        { name: 'Daftar Hutang', icon: List, path: '/hutang/list' },
        { name: 'Pembayaran Hutang', icon: CreditCard, path: '/purchase/ap-payments' },
        { name: 'Tambah Pembayaran Hutang', icon: Plus, path: '/purchase/ap-payments/add' },
        { name: 'Umur Hutang', icon: Clock, path: '/hutang/aging' },
      ]
    },

    // ============================================================
    // PIUTANG (AR) - iPOS Style - PRIMARY MENU untuk Piutang
    // ============================================================
    {
      name: 'Piutang',
      icon: CreditCard,
      roles: ['owner', 'admin', 'finance'],
      submenu: [
        { name: 'Daftar Piutang', icon: List, path: '/piutang/list' },
        { name: 'Pembayaran Piutang', icon: Wallet, path: '/sales/ar-payments' },
        { name: 'Tambah Pembayaran Piutang', icon: Plus, path: '/sales/ar-payments/add' },
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
    // LAPORAN - Menggunakan Report Center sebagai primary
    // ============================================================
    {
      name: 'Laporan',
      icon: BarChart3,
      roles: ['owner', 'admin', 'supervisor', 'finance'],
      submenu: [
        { name: 'Report Center', icon: FileBarChart, path: '/report-center' },
        { divider: true, label: 'Quick Reports' },
        { name: 'Laporan Penjualan', icon: TrendingUp, path: '/reports/sales' },
        { name: 'Laporan Pembelian', icon: Truck, path: '/reports/purchase' },
        { name: 'Laporan Stok', icon: Boxes, path: '/reports/inventory' },
        // REMOVED: Laporan Kartu Stok - duplicate dengan Inventory > Kartu Stok (TASK 1 - 2026-03-15)
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
    // APPROVAL CENTER - Phase 3 (HIDDEN - only show if workflow enabled)
    // ============================================================
    // HIDDEN: Modul ini digunakan hanya jika workflow bisnis memerlukan
    // {
    //   name: 'Approval Center',
    //   icon: FileCheck,
    //   path: '/approval-center',
    //   roles: ['owner', 'admin', 'supervisor', 'finance']
    // },

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
    // HIDDEN: WarehouseControl - overlap dengan Inventory (Phase A Cleanup 2026-03-13)
    // BRANCH INVENTORY CONTROL - (Renamed from Warehouse Control)
    // Karena sistem menggunakan konsep: Gudang = Cabang
    // ============================================================
    // {
    //   name: 'Branch Inventory Control',
    //   icon: Warehouse,
    //   path: '/warehouse-control',
    //   roles: ['owner', 'admin', 'inventory']
    // },

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
    // SALES TARGET - Phase 3 (HIDDEN - only show if needed)
    // ============================================================
    // HIDDEN: Modul ini digunakan hanya jika workflow bisnis memerlukan
    // {
    //   name: 'Sales Target',
    //   icon: Target,
    //   path: '/sales-target',
    //   roles: ['owner', 'admin', 'sales_manager']
    // },

    // ============================================================
    // COMMISSION ENGINE - Phase 3 (HIDDEN - only show if needed)
    // ============================================================
    // HIDDEN: Modul ini digunakan hanya jika workflow bisnis memerlukan
    // {
    //   name: 'Komisi',
    //   icon: Wallet,
    //   path: '/commission',
    //   roles: ['owner', 'admin', 'finance_manager']
    // },

    // ============================================================
    // CASH CONTROL - Phase 3
    // ============================================================
    {
      name: 'Kontrol Kas',
      icon: BanknoteIcon,
      path: '/cash-control',
      roles: ['owner', 'admin', 'kasir', 'supervisor', 'finance_manager']
    },

    // ============================================================
    // KPI DASHBOARD - Phase 5
    // ============================================================
    {
      name: 'KPI Dashboard',
      icon: BarChart3,
      path: '/kpi-dashboard',
      roles: ['owner', 'admin', 'finance_manager', 'sales_manager']
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
        { name: 'Manajemen Tenant', icon: Database, path: '/settings/tenants', roles: ['owner', 'super_admin'] },
        { divider: true },
        { name: 'Printer & Struk', icon: Printer, path: '/settings/printer' },
        { name: 'Import Excel', icon: Upload, path: '/settings/import' },
        { name: 'Export Excel', icon: Download, path: '/settings/export' },
        { divider: true },
        { name: 'Log Aktivitas', icon: Clock, path: '/settings/activity-log' },
        { name: 'Backup & Restore', icon: HardDrive, path: '/settings/backup' },
        { name: 'Data Rescue', icon: Database, path: '/settings/data-rescue' },
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
        // HIDDEN: WarRoomV2 - Phase 6 AI HOLD (Phase A Cleanup 2026-03-13)
        // { name: 'War Room V2', icon: Activity, path: '/war-room-v2' },
        // HIDDEN: AIWarRoomSuper - Phase 6 AI HOLD (Phase A Cleanup 2026-03-13)
        // { name: 'AI War Room Super', icon: Shield, path: '/ai-warroom-super' },
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

  // Filter menus based on RBAC permissions - SYNCHRONIZED WITH DATABASE
  const filteredMenus = menuStructure.filter(item => {
    const userRole = user?.role?.toLowerCase();
    
    // Super admin / owner = full access
    if (permissions?.all_permissions || 
        userRole === 'owner' || 
        userRole === 'pemilik' || 
        userRole === 'super_admin' ||
        userRole === 'admin') {
      return true;
    }
    
    // KASIR - STRICTLY LIMITED ACCESS
    if (userRole === 'kasir' || userRole === 'cashier') {
      const kasirAllowed = getKasirAllowedMenus();
      return kasirAllowed.includes(item.name);
    }
    
    // Check using RBAC helper
    if (!shouldShowMenu(userRole, item.name)) {
      return false;
    }
    
    // Legacy role check
    const roleAllowed = item.roles?.includes(userRole);
    if (!roleAllowed) return false;
    
    // Module-based check
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
                          : subItem.highlight 
                            ? 'text-green-400 hover:bg-green-900/20 hover:text-green-300 bg-green-900/10 border border-green-700/30'
                            : 'text-gray-400 hover:bg-red-900/10 hover:text-red-200'
                      }`
                    }
                  >
                    <subItem.icon className={`h-4 w-4 ${subItem.highlight ? 'text-green-400' : ''}`} />
                    <span>{subItem.name}</span>
                    {subItem.badge && (
                      <span className="ml-auto px-1.5 py-0.5 text-[10px] font-bold bg-green-600 text-white rounded">
                        {subItem.badge}
                      </span>
                    )}
                    {subItem.highlight && (
                      <span className="ml-auto px-1.5 py-0.5 text-[10px] font-bold bg-green-600 text-white rounded">
                        NEW
                      </span>
                    )}
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
      {/* SHIFT WARNING MODAL - Kasir tidak boleh logout sebelum tutup shift */}
      {showShiftWarning && (
        <div className="fixed inset-0 bg-black/70 z-[100] flex items-center justify-center p-4">
          <div className="bg-[#1a1012] border border-red-700/50 rounded-xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-12 w-12 rounded-full bg-red-900/30 flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-red-200">Shift Masih Aktif</h3>
                <p className="text-sm text-gray-400">Anda tidak dapat logout</p>
              </div>
            </div>
            <p className="text-gray-300 mb-6">
              Anda harus menutup shift kasir terlebih dahulu sebelum logout. 
              Silakan ke halaman <strong className="text-amber-300">Kontrol Kas</strong> untuk menutup shift.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowShiftWarning(false)}
                className="flex-1 px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleCloseShiftAndLogout}
                className="flex-1 px-4 py-2 bg-red-700 text-white rounded-lg hover:bg-red-600 transition-colors"
              >
                Tutup Shift
              </button>
            </div>
          </div>
        </div>
      )}

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
