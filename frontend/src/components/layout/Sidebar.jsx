import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, ShoppingCart, Package, Boxes, Users, Building2, 
  Settings, LogOut, DollarSign, Truck, UserCog, Warehouse,
  BarChart3, Calculator, Brain, Shield, Sparkles
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const Sidebar = ({ isOpen, setIsOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: '/dashboard', roles: ['owner', 'admin', 'supervisor', 'cashier', 'finance', 'inventory'] },
    { name: 'Hallo AI', icon: Sparkles, path: '/hallo-ai', roles: ['owner', 'admin', 'supervisor', 'cashier', 'finance', 'inventory'], highlight: true },
    { name: 'Kasir', icon: ShoppingCart, path: '/kasir', roles: ['owner', 'admin', 'supervisor', 'cashier'] },
    { name: 'Produk', icon: Package, path: '/produk', roles: ['owner', 'admin', 'supervisor', 'cashier', 'inventory'] },
    { name: 'Stok', icon: Boxes, path: '/stok', roles: ['owner', 'admin', 'supervisor', 'cashier', 'inventory'] },
    { name: 'Pembelian', icon: Truck, path: '/pembelian', roles: ['owner', 'admin', 'supervisor', 'inventory'] },
    { name: 'Supplier', icon: Warehouse, path: '/supplier', roles: ['owner', 'admin', 'supervisor', 'inventory'] },
    { name: 'Pelanggan', icon: Users, path: '/pelanggan', roles: ['owner', 'admin', 'supervisor', 'cashier'] },
    { name: 'Keuangan', icon: DollarSign, path: '/keuangan', roles: ['owner', 'admin', 'finance'] },
    { name: 'Akuntansi', icon: Calculator, path: '/akuntansi', roles: ['owner', 'admin', 'finance'] },
    { name: 'Laporan', icon: BarChart3, path: '/laporan', roles: ['owner', 'admin', 'supervisor', 'cashier', 'finance'] },
    { name: 'AI Bisnis', icon: Brain, path: '/ai-bisnis', roles: ['owner', 'admin', 'supervisor', 'cashier', 'finance'] },
    { name: 'Cabang', icon: Building2, path: '/cabang', roles: ['owner', 'admin'] },
    { name: 'Pengguna', icon: UserCog, path: '/pengguna', roles: ['owner', 'admin'] },
    { name: 'Hak Akses', icon: Shield, path: '/hak-akses', roles: ['owner', 'admin'] },
    { name: 'Pengaturan', icon: Settings, path: '/pengaturan', roles: ['owner', 'admin', 'supervisor'] },
  ];

  const filteredNavItems = navItems.filter(item => 
    item.roles.includes(user?.role || 'cashier')
  );

  const roleLabels = {
    owner: 'Pemilik',
    admin: 'Administrator',
    supervisor: 'Supervisor',
    cashier: 'Kasir',
    finance: 'Keuangan',
    inventory: 'Gudang'
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
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-gradient-to-b from-[#0a0608] to-[#120a0c] border-r border-red-900/20 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-red-900/20">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent">
              OCB AI TITAN
            </h1>
            <p className="text-xs text-red-300/50 mt-1">Enterprise Retail AI System</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-1">
            {filteredNavItems.map((item) => (
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
            ))}
          </nav>

          {/* User Info & Logout */}
          <div className="p-4 border-t border-red-900/20 bg-red-950/20">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-red-600 to-amber-500 flex items-center justify-center text-white font-semibold shadow-lg shadow-red-900/30">
                {user?.name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-amber-100 truncate">{user?.name}</p>
                <p className="text-xs text-red-300/50">{roleLabels[user?.role] || user?.role} • {user?.branch?.code || 'HQ'}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
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
