import React, { useState, useEffect } from 'react';
import { Menu, Bell, Search, Moon, Sun, Database, Building2, Store, Truck, Shirt, Monitor } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';

import { getApiUrl } from '../../utils/apiConfig';
const API_URL = getApiUrl();

// Icon mapping for tenant types
const tenantIconMap = {
  building: Building2,
  store: Store,
  truck: Truck,
  shirt: Shirt,
  monitor: Monitor,
};

const Header = ({ sidebarOpen, setSidebarOpen }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [tenantInfo, setTenantInfo] = useState(null);

  // Fetch current tenant info on mount and when window gains focus
  useEffect(() => {
    fetchTenantInfo();
    
    // Refresh on window focus (for tenant switch detection)
    const handleFocus = () => fetchTenantInfo();
    window.addEventListener('focus', handleFocus);
    
    // Also listen for custom event when tenant switches
    const handleTenantSwitch = () => fetchTenantInfo();
    window.addEventListener('tenant-switched', handleTenantSwitch);
    
    return () => {
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('tenant-switched', handleTenantSwitch);
    };
  }, []);

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

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-emerald-600/20 text-emerald-400 border-emerald-600/30';
      case 'test': return 'bg-yellow-600/20 text-yellow-400 border-yellow-600/30';
      case 'internal': return 'bg-gray-600/20 text-gray-400 border-gray-600/30';
      default: return 'bg-red-600/20 text-red-400 border-red-600/30';
    }
  };

  // Get tenant icon
  const TenantIcon = tenantIconMap[tenantInfo?.icon] || Database;

  return (
    <header className="h-16 border-b border-red-900/20 bg-gradient-to-r from-[#0a0608]/90 to-[#120a0c]/90 backdrop-blur-xl px-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="lg:hidden text-red-200 hover:bg-red-900/20"
        >
          <Menu className="h-5 w-5" />
        </Button>
        
        {/* Tenant Info Badge */}
        {tenantInfo && (
          <div 
            data-testid="tenant-badge"
            className="hidden sm:flex items-center gap-3 px-3 py-1.5 bg-[#1a1214] rounded-lg border border-red-900/30"
          >
            <div 
              className="p-1.5 rounded-md"
              style={{ backgroundColor: `${tenantInfo.color}20` }}
            >
              <TenantIcon 
                className="h-4 w-4" 
                style={{ color: tenantInfo.color }}
              />
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-400">Tenant</span>
              <span className="text-sm font-medium text-amber-100">{tenantInfo.tenant_name}</span>
            </div>
            <div className="h-8 w-px bg-red-900/30" />
            <div className="flex flex-col">
              <span className="text-xs text-gray-400">Database</span>
              <span className="text-xs font-mono text-amber-200/70">{tenantInfo.database}</span>
            </div>
            <span className={`px-2 py-0.5 text-[10px] uppercase font-semibold rounded-full border ${getStatusColor(tenantInfo.status)}`}>
              {tenantInfo.status}
            </span>
          </div>
        )}
        
        <div className="hidden lg:flex items-center gap-2 px-3 py-2 bg-red-950/30 backdrop-blur-sm rounded-lg border border-red-900/30">
          <Search className="h-4 w-4 text-red-400/60" />
          <input
            type="text"
            placeholder="Search..."
            className="bg-transparent border-none outline-none text-sm w-48 xl:w-64 text-amber-50 placeholder:text-red-300/40"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Mobile Tenant Badge */}
        {tenantInfo && (
          <div 
            className="sm:hidden flex items-center gap-1.5 px-2 py-1 bg-[#1a1214] rounded-md border border-red-900/30"
          >
            <Database className="h-3 w-3 text-amber-500" />
            <span className="text-xs font-mono text-amber-200/70">{tenantInfo.database}</span>
          </div>
        )}
        
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          data-testid="theme-toggle"
          className="text-red-200 hover:bg-red-900/20"
        >
          {theme === 'dark' ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </Button>

        <Button variant="ghost" size="icon" className="text-red-200 hover:bg-red-900/20">
          <Bell className="h-5 w-5" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-red-900/20 transition-all duration-200">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-red-600 to-amber-500 flex items-center justify-center text-white text-sm font-semibold shadow-lg shadow-red-900/30">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-amber-100">{user?.full_name}</p>
                <p className="text-xs text-red-300/50 capitalize">{user?.role}</p>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-red-950/95 border-red-900/30">
            <DropdownMenuItem className="text-amber-100 focus:bg-red-900/30">Profile</DropdownMenuItem>
            <DropdownMenuItem className="text-amber-100 focus:bg-red-900/30">Settings</DropdownMenuItem>
            <DropdownMenuSeparator className="bg-red-900/30" />
            <DropdownMenuItem onClick={logout} data-testid="logout-button" className="text-red-300 focus:bg-red-900/30">
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

export default Header;