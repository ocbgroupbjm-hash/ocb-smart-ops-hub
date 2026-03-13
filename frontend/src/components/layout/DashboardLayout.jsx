import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { Menu, AlertTriangle, Clock, Database, Building2, Store, Truck, Shirt, Monitor } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Icon mapping for tenant types
const tenantIconMap = {
  building: Building2,
  store: Store,
  truck: Truck,
  shirt: Shirt,
  monitor: Monitor,
};

// Get status color
const getStatusColor = (status) => {
  switch (status) {
    case 'active': return 'bg-emerald-600/20 text-emerald-400 border-emerald-600/30';
    case 'test': return 'bg-yellow-600/20 text-yellow-400 border-yellow-600/30';
    case 'internal': return 'bg-gray-600/20 text-gray-400 border-gray-600/30';
    default: return 'bg-red-600/20 text-red-400 border-red-600/30';
  }
};

export const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [shiftStatus, setShiftStatus] = useState({ loading: true, hasActiveShift: false });
  const [showShiftBanner, setShowShiftBanner] = useState(false);
  const [tenantInfo, setTenantInfo] = useState(null);
  
  const userRole = user?.role?.toLowerCase();
  const isKasir = userRole === 'kasir' || userRole === 'cashier';

  // Fetch current tenant info
  useEffect(() => {
    const fetchTenantInfo = async () => {
      try {
        const res = await fetch(`${API_URL}/api/system/current-tenant`);
        if (res.ok) {
          const data = await res.json();
          setTenantInfo(data);
        }
      } catch (err) {
        console.error('Failed to fetch tenant info:', err);
      }
    };
    
    fetchTenantInfo();
    
    // Listen for tenant switch events
    const handleTenantSwitch = () => fetchTenantInfo();
    window.addEventListener('tenant-switched', handleTenantSwitch);
    window.addEventListener('focus', handleTenantSwitch);
    
    return () => {
      window.removeEventListener('tenant-switched', handleTenantSwitch);
      window.removeEventListener('focus', handleTenantSwitch);
    };
  }, []);

  // Check shift status for kasir
  useEffect(() => {
    const checkShift = async () => {
      if (!isKasir) {
        setShiftStatus({ loading: false, hasActiveShift: true });
        return;
      }

      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/api/cash-control/shift/check`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setShiftStatus({
          loading: false,
          hasActiveShift: response.data.has_active_shift,
          shift: response.data.shift
        });
        setShowShiftBanner(!response.data.has_active_shift);
      } catch (error) {
        setShiftStatus({ loading: false, hasActiveShift: false });
        setShowShiftBanner(true);
      }
    };

    checkShift();
  }, [isKasir, location.pathname]);
  
  // Full-screen pages (no sidebar)
  const fullScreenPages = ['/pos', '/warroom', '/ai-sales'];
  const isFullScreen = fullScreenPages.includes(location.pathname);

  // GUARD: Block kasir from accessing certain routes without shift
  const shiftRequiredRoutes = ['/kasir', '/sales/add', '/sales/orders/add'];
  const currentPath = location.pathname;
  const needsShift = shiftRequiredRoutes.some(route => currentPath.startsWith(route));

  if (isFullScreen) {
    return <Outlet />;
  }

  // KASIR SHIFT BLOCK - jika kasir mencoba akses transaksi tanpa shift
  if (isKasir && needsShift && !shiftStatus.loading && !shiftStatus.hasActiveShift) {
    return (
      <div className="flex h-screen bg-[#0a0608] text-gray-100">
        <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
        <main className="flex-1 overflow-auto">
          <div className="flex flex-col items-center justify-center h-full p-8">
            <div className="bg-red-900/30 border border-red-700/50 rounded-xl p-8 max-w-lg text-center">
              <div className="h-20 w-20 rounded-full bg-red-900/50 flex items-center justify-center mx-auto mb-6">
                <AlertTriangle className="h-10 w-10 text-red-400" />
              </div>
              <h2 className="text-2xl font-bold text-red-200 mb-3">Shift Belum Dibuka</h2>
              <p className="text-gray-400 mb-6">
                Anda harus membuka shift kasir terlebih dahulu sebelum dapat melakukan transaksi penjualan.
              </p>
              <div className="flex items-center justify-center gap-2 text-amber-300 mb-6">
                <Clock className="h-5 w-5" />
                <span>Buka shift di halaman Kontrol Kas</span>
              </div>
              <button
                onClick={() => navigate('/cash-control')}
                className="px-8 py-3 bg-red-700 text-white rounded-lg hover:bg-red-600 transition-colors font-semibold text-lg"
              >
                Buka Shift Sekarang
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#0a0608] text-gray-100">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      
      <main className="flex-1 overflow-auto">
        {/* Desktop Header with Tenant Info */}
        <div className="hidden lg:flex items-center justify-between px-6 py-3 border-b border-red-900/20 bg-gradient-to-r from-[#0a0608]/90 to-[#120a0c]/90 backdrop-blur-xl">
          {/* Tenant Badge */}
          {tenantInfo && (
            <div 
              data-testid="tenant-badge"
              className="flex items-center gap-3 px-4 py-2 bg-[#1a1214] rounded-lg border border-red-900/30"
            >
              <div 
                className="p-2 rounded-md"
                style={{ backgroundColor: `${tenantInfo.color}20` }}
              >
                {React.createElement(tenantIconMap[tenantInfo.icon] || Database, {
                  className: "h-5 w-5",
                  style: { color: tenantInfo.color }
                })}
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-gray-400">Tenant</span>
                <span className="text-sm font-semibold text-amber-100">{tenantInfo.tenant_name}</span>
              </div>
              <div className="h-10 w-px bg-red-900/30" />
              <div className="flex flex-col">
                <span className="text-xs text-gray-400">Database</span>
                <span className="text-sm font-mono text-amber-200/80">{tenantInfo.database}</span>
              </div>
              <div className="h-10 w-px bg-red-900/30" />
              <div className="flex flex-col">
                <span className="text-xs text-gray-400">Type</span>
                <span className="text-sm text-gray-300">{tenantInfo.tenant_type}</span>
              </div>
              <span className={`ml-2 px-2.5 py-1 text-xs uppercase font-bold rounded-full border ${getStatusColor(tenantInfo.status)}`}>
                {tenantInfo.status}
              </span>
            </div>
          )}
          
          {/* Blueprint Version for Admin */}
          {tenantInfo && user?.role === 'owner' && (
            <div className="text-xs text-gray-500">
              Blueprint v{tenantInfo.blueprint_version}
            </div>
          )}
        </div>
        
        {/* Mobile Header */}
        <div className="lg:hidden flex items-center justify-between p-4 border-b border-red-900/20 bg-[#0a0608]">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 hover:bg-red-900/20 rounded-lg"
          >
            <Menu className="h-6 w-6" />
          </button>
          
          {/* Mobile Tenant Badge */}
          {tenantInfo && (
            <div className="flex items-center gap-2 px-2 py-1 bg-[#1a1214] rounded-md border border-red-900/30">
              <Database className="h-4 w-4 text-amber-500" />
              <span className="text-xs font-mono text-amber-200/80">{tenantInfo.database}</span>
              <span className={`px-1.5 py-0.5 text-[10px] uppercase font-bold rounded ${getStatusColor(tenantInfo.status)}`}>
                {tenantInfo.status}
              </span>
            </div>
          )}
          
          <div className="w-10" />
        </div>

        {/* KASIR SHIFT BANNER - Warning jika belum buka shift */}
        {isKasir && showShiftBanner && !shiftStatus.loading && (
          <div className="bg-red-900/30 border-b border-red-700/50 px-6 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-red-400" />
                <span className="text-red-200 font-medium">
                  Anda belum membuka shift kasir. Transaksi tidak dapat dilakukan.
                </span>
              </div>
              <button
                onClick={() => navigate('/cash-control')}
                className="px-4 py-1.5 bg-red-700 text-white rounded-lg hover:bg-red-600 transition-colors text-sm font-medium"
              >
                Buka Shift
              </button>
            </div>
          </div>
        )}
        
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
