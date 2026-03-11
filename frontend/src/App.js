import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { PermissionProvider } from './contexts/PermissionContext';
import { Toaster } from './components/ui/sonner';
import { DashboardLayout } from './components/layout/DashboardLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import POS from './pages/POS';
import Products from './pages/Products';
import Inventory from './pages/Inventory';
import Purchase from './pages/Purchase';
import PurchaseModule from './pages/PurchaseModule';
import Suppliers from './pages/Suppliers';
import Customers from './pages/Customers';
import Finance from './pages/Finance';
import Accounting from './pages/Accounting';
import Reports from './pages/Reports';
import Branches from './pages/Branches';
import Users from './pages/Users';
import RolePermission from './pages/RolePermission';
import AIBusiness from './pages/AIBusiness';
import HalloAI from './pages/HalloAI';
import Settings from './pages/Settings';
import BusinessManager from './pages/BusinessManager';

// SUPER AI Pages
import Warroom from './pages/Warroom';
import AISales from './pages/AISales';

// SUPER ERP Pages
import SetoranHarian from './pages/operasional/SetoranHarian';
import SelisihKas from './pages/SelisihKas';
import Employees from './pages/Employees';
import Absensi from './pages/Absensi';
import Payroll from './pages/Payroll';
import WarRoomV2 from './pages/WarRoomV2';
import ERPDashboard from './pages/ERPDashboard';
import MasterERP from './pages/MasterERP';
import ERPReports from './pages/ERPReports';

// OCB TITAN AI Pages
import GlobalMap from './pages/GlobalMap';
import DataExport from './pages/DataExport';
import KPIPerformance from './pages/KPIPerformance';
import AICommandCenter from './pages/AICommandCenter';
import CRMAI from './pages/CRMAI';

// OCB TITAN AI Phase 2 Pages
import AdvancedExport from './pages/AdvancedExport';
import ImportSystem from './pages/ImportSystem';
import WhatsAppAlerts from './pages/WhatsAppAlerts';
import WarRoomAlertPanel from './pages/WarRoomAlertPanel';
import HRManagement from './pages/HRManagement';

// OCB TITAN AI Phase 3 Pages - AI Super War Room
import CFODashboard from './pages/CFODashboard';
import AIWarRoomSuper from './pages/AIWarRoomSuper';

// OCB TITAN AI Phase 4 Pages - HR & Performance
import AIPerformance from './pages/AIPerformance';
import PayrollAuto from './pages/PayrollAuto';

// Master Data Pages
import { 
  MasterItems, MasterCategories, MasterUnits, MasterBrands, 
  MasterWarehouses, MasterSuppliers, MasterCustomers, MasterSalesPersons,
  MasterCustomerGroups, MasterRegions, MasterBanks, MasterEmoney,
  MasterShippingCosts, MasterDiscounts, MasterPromotions
} from './pages/master';

// Purchase Pages
import { 
  PurchaseOrders, PurchaseList, PurchaseReceiving, 
  PurchasePayments, PurchaseReturns, PurchasePriceHistory 
} from './pages/purchase';

// Sales Pages
import { SalesList, SalesReturns, SalesDelivery } from './pages/sales';

// Inventory Pages
import { StockCards, StockMovements, StockTransfers, StockOpname, KartuStok } from './pages/inventory';
import SerialNumbers from './pages/inventory/SerialNumbers';
import ProductAssembly from './pages/inventory/ProductAssembly';

// Settings Pages
import { PrinterSettings, RBACManagement } from './pages/settings';

// Accounting Pages
import ChartOfAccounts from './pages/accounting/ChartOfAccounts';
import JournalEntries from './pages/accounting/JournalEntries';
import GeneralLedger from './pages/accounting/GeneralLedger';
import CashTransactions from './pages/accounting/CashTransactions';
import TrialBalance from './pages/accounting/TrialBalance';
import BalanceSheet from './pages/accounting/BalanceSheet';
import IncomeStatement from './pages/accounting/IncomeStatement';
import CashFlow from './pages/accounting/CashFlow';
import AccountsReceivable from './pages/accounting/AccountsReceivable';
import AccountsPayable from './pages/accounting/AccountsPayable';
import FinancialReports from './pages/accounting/FinancialReports';

// Approval Pages
import ApprovalCenter from './pages/approval/ApprovalCenter';

import './index.css';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0608]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" />;
};

// Access denied component
const AccessDenied = () => (
  <div className="flex flex-col items-center justify-center h-64 text-center">
    <div className="text-6xl mb-4">🚫</div>
    <h2 className="text-2xl font-bold text-red-400 mb-2">Akses Ditolak</h2>
    <p className="text-gray-400">Anda tidak memiliki izin untuk mengakses halaman ini.</p>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <PermissionProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <PrivateRoute>
                  <DashboardLayout />
                </PrivateRoute>
              }
            >
            <Route index element={<Navigate to="/dashboard" />} />
            <Route path="dashboard" element={<Dashboard />} />
            
            {/* SUPER AI Routes */}
            <Route path="warroom" element={<Warroom />} />
            <Route path="ai-sales" element={<AISales />} />
            <Route path="war-room-v2" element={<WarRoomV2 />} />
            
            {/* OCB TITAN AI Routes */}
            <Route path="global-map" element={<GlobalMap />} />
            <Route path="data-export" element={<DataExport />} />
            <Route path="kpi-performance" element={<KPIPerformance />} />
            <Route path="ai-command-center" element={<AICommandCenter />} />
            <Route path="crm-ai" element={<CRMAI />} />
            
            {/* OCB TITAN AI Phase 2 Routes */}
            <Route path="advanced-export" element={<AdvancedExport />} />
            <Route path="import-system" element={<ImportSystem />} />
            <Route path="whatsapp-alerts" element={<WhatsAppAlerts />} />
            <Route path="warroom-alerts" element={<WarRoomAlertPanel />} />
            
            {/* OCB TITAN AI Phase 3 Routes - AI Super War Room */}
            <Route path="cfo-dashboard" element={<CFODashboard />} />
            <Route path="ai-warroom-super" element={<AIWarRoomSuper />} />
            
            {/* OCB TITAN AI Phase 4 Routes - HR & Performance */}
            <Route path="ai-performance" element={<AIPerformance />} />
            <Route path="payroll-auto" element={<PayrollAuto />} />
            
            {/* SUPER ERP Routes */}
            <Route path="setoran-harian" element={<SetoranHarian />} />
            <Route path="selisih-kas" element={<SelisihKas />} />
            <Route path="employees" element={<Employees />} />
            <Route path="absensi" element={<Absensi />} />
            <Route path="payroll" element={<Payroll />} />
            <Route path="erp-dashboard" element={<ERPDashboard />} />
            
            {/* Master ERP Routes */}
            <Route path="master/shifts" element={<MasterERP />} />
            <Route path="master/jabatan" element={<MasterERP />} />
            <Route path="master/lokasi-absensi" element={<MasterERP />} />
            <Route path="master/payroll-rules" element={<MasterERP />} />
            <Route path="master-erp" element={<MasterERP />} />
            <Route path="erp-reports" element={<ERPReports />} />
            <Route path="hr-management" element={<HRManagement />} />
            
            <Route path="kasir" element={<POS />} />
            <Route path="produk" element={<Products />} />
            <Route path="stok" element={<Inventory />} />
            <Route path="pembelian" element={<Purchase />} />
            <Route path="supplier" element={<Suppliers />} />
            <Route path="pelanggan" element={<Customers />} />
            <Route path="keuangan" element={<Finance />} />
            <Route path="akuntansi" element={<Accounting />} />
            <Route path="laporan" element={<Reports />} />
            <Route path="ai-bisnis" element={<AIBusiness />} />
            <Route path="hallo-ai" element={<HalloAI />} />
            <Route path="cabang" element={<Branches />} />
            <Route path="pengguna" element={<Users />} />
            <Route path="hak-akses" element={<RolePermission />} />
            <Route path="pengaturan" element={<Settings />} />
            <Route path="akses-ditolak" element={<AccessDenied />} />
            
            {/* Master Data Routes */}
            <Route path="master/items" element={<MasterItems />} />
            <Route path="master/categories" element={<MasterCategories />} />
            <Route path="master/units" element={<MasterUnits />} />
            <Route path="master/brands" element={<MasterBrands />} />
            <Route path="master/warehouses" element={<MasterWarehouses />} />
            <Route path="master/suppliers" element={<MasterSuppliers />} />
            <Route path="master/customers" element={<MasterCustomers />} />
            <Route path="master/sales-persons" element={<MasterSalesPersons />} />
            <Route path="master/customer-groups" element={<MasterCustomerGroups />} />
            <Route path="master/customer-points" element={<MasterCustomerGroups />} />
            <Route path="master/regions" element={<MasterRegions />} />
            <Route path="master/emoney" element={<MasterEmoney />} />
            <Route path="master/banks" element={<MasterBanks />} />
            <Route path="master/shipping-costs" element={<MasterShippingCosts />} />
            <Route path="master/stock-cards" element={<Inventory />} />
            <Route path="master/discounts" element={<MasterDiscounts />} />
            <Route path="master/promotions" element={<MasterPromotions />} />
            
            {/* Purchase Routes */}
            <Route path="purchase" element={<PurchaseModule />} />
            <Route path="purchase/orders" element={<PurchaseOrders />} />
            <Route path="purchase/list" element={<PurchaseList />} />
            <Route path="purchase/receiving" element={<PurchaseReceiving />} />
            <Route path="purchase/price-history" element={<PurchasePriceHistory />} />
            <Route path="purchase/payments" element={<PurchasePayments />} />
            <Route path="purchase/payment-status" element={<PurchasePayments />} />
            <Route path="purchase/returns" element={<PurchaseReturns />} />
            
            {/* Sales Routes */}
            <Route path="sales/orders" element={<POS />} />
            <Route path="sales/list" element={<SalesList />} />
            <Route path="sales/cashier-sales" element={<POS />} />
            <Route path="sales/price-history" element={<Products />} />
            <Route path="sales/trade-in" element={<POS />} />
            <Route path="sales/payments" element={<Finance />} />
            <Route path="sales/payment-status" element={<Finance />} />
            <Route path="sales/returns" element={<SalesReturns />} />
            <Route path="sales/points" element={<Customers />} />
            <Route path="sales/deliveries" element={<SalesDelivery />} />
            
            {/* Inventory Routes */}
            <Route path="inventory/stock-list" element={<Inventory />} />
            <Route path="inventory/stock-cards" element={<StockCards />} />
            <Route path="inventory/kartu-stok" element={<KartuStok />} />
            <Route path="inventory/stock-in" element={<StockMovements />} />
            <Route path="inventory/stock-out" element={<StockMovements />} />
            <Route path="inventory/transfer" element={<StockTransfers />} />
            <Route path="inventory/mutations" element={<StockMovements />} />
            <Route path="inventory/opname" element={<StockOpname />} />
            <Route path="inventory/serial-numbers" element={<SerialNumbers />} />
            <Route path="inventory/assemblies" element={<ProductAssembly />} />
            
            {/* Accounting Routes */}
            <Route path="accounting/coa" element={<ChartOfAccounts />} />
            <Route path="accounting/cash-in" element={<CashTransactions />} />
            <Route path="accounting/cash-out" element={<CashTransactions />} />
            <Route path="accounting/cash-transfer" element={<CashTransactions />} />
            <Route path="accounting/customer-deposit" element={<CashTransactions />} />
            <Route path="accounting/supplier-deposit" element={<CashTransactions />} />
            <Route path="accounting/journals" element={<JournalEntries />} />
            <Route path="accounting/ledger" element={<GeneralLedger />} />
            <Route path="accounting/trial-balance" element={<TrialBalance />} />
            <Route path="accounting/balance-sheet" element={<BalanceSheet />} />
            <Route path="accounting/income-statement" element={<IncomeStatement />} />
            <Route path="accounting/cash-flow" element={<CashFlow />} />
            <Route path="accounting/opening-balance" element={<ChartOfAccounts />} />
            <Route path="accounting/year-end" element={<ChartOfAccounts />} />
            <Route path="accounting/coa-settings" element={<ChartOfAccounts />} />
            <Route path="accounting/receivables" element={<AccountsReceivable />} />
            <Route path="accounting/payables" element={<AccountsPayable />} />
            <Route path="accounting/financial-reports" element={<FinancialReports />} />
            
            {/* Approval Routes */}
            <Route path="approval-center" element={<ApprovalCenter />} />
            
            {/* Reports Routes */}
            <Route path="reports/sales" element={<Reports />} />
            <Route path="reports/purchase" element={<Reports />} />
            <Route path="reports/inventory" element={<Reports />} />
            <Route path="reports/best-sellers" element={<Reports />} />
            <Route path="reports/payables" element={<Reports />} />
            <Route path="reports/receivables" element={<Reports />} />
            <Route path="reports/cash" element={<Reports />} />
            <Route path="reports/profit-loss" element={<Reports />} />
            <Route path="reports/branches" element={<Reports />} />
            <Route path="reports/cashiers" element={<Reports />} />
            <Route path="reports/suppliers" element={<Reports />} />
            <Route path="reports/customers" element={<Reports />} />
            
            {/* Settings Routes */}
            <Route path="settings/users" element={<Users />} />
            <Route path="settings/roles" element={<RBACManagement />} />
            <Route path="rbac" element={<RBACManagement />} />
            <Route path="settings/company" element={<Settings />} />
            <Route path="settings/general" element={<Settings />} />
            <Route path="settings/branches" element={<Branches />} />
            <Route path="settings/periods" element={<Settings />} />
            <Route path="settings/numbering" element={<Settings />} />
            <Route path="settings/printer" element={<PrinterSettings />} />
            <Route path="settings/theme" element={<Settings />} />
            <Route path="settings/import" element={<Settings />} />
            <Route path="settings/export" element={<Settings />} />
            <Route path="settings/backup" element={<Settings />} />
            <Route path="settings/activity-log" element={<Settings />} />
            <Route path="settings/system-analysis" element={<Settings />} />
            <Route path="settings/help" element={<Settings />} />
            <Route path="settings/info" element={<Settings />} />
            <Route path="settings/business" element={<BusinessManager />} />
            <Route path="kelola-bisnis" element={<BusinessManager />} />
          </Route>
        </Routes>
        </BrowserRouter>
      </PermissionProvider>
      <Toaster position="top-right" />
    </AuthProvider>
  );
}

export default App;
