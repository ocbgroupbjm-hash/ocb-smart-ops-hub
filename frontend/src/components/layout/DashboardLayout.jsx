import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import { Menu } from 'lucide-react';

export const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  
  // Full-screen pages (no sidebar)
  const fullScreenPages = ['/pos'];
  const isFullScreen = fullScreenPages.includes(location.pathname);

  if (isFullScreen) {
    return <Outlet />;
  }

  return (
    <div className="flex h-screen bg-[#0a0608] text-gray-100">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      
      <main className="flex-1 overflow-auto">
        {/* Mobile Header */}
        <div className="lg:hidden flex items-center justify-between p-4 border-b border-red-900/20 bg-[#0a0608]">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 hover:bg-red-900/20 rounded-lg"
          >
            <Menu className="h-6 w-6" />
          </button>
          <h1 className="text-lg font-bold text-amber-100">OCB TITAN</h1>
          <div className="w-10" />
        </div>
        
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
