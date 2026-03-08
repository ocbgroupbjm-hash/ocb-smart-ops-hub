import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Bot, 
  Users, 
  Store, 
  BarChart3, 
  Package, 
  BookOpen,
  Settings,
  X
} from 'lucide-react';
import { cn } from '../../lib/utils';

const Sidebar = ({ isOpen, setIsOpen }) => {
  const navItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
    { name: 'AI Chat', icon: Bot, path: '/ai-chat' },
    { name: 'CRM', icon: Users, path: '/crm' },
    { name: 'Branches', icon: Store, path: '/branches' },
    { name: 'Analytics', icon: BarChart3, path: '/analytics' },
    { name: 'Inventory', icon: Package, path: '/inventory' },
    { name: 'Knowledge Base', icon: BookOpen, path: '/knowledge' },
    { name: 'Settings', icon: Settings, path: '/settings' },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed lg:static inset-y-0 left-0 z-50 w-64 bg-gradient-to-b from-[#0a0608] to-[#120a0c] border-r border-red-900/20 transform transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-6 border-b border-red-900/20">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent">
                OCB AI
              </h1>
              <p className="text-xs text-red-300/50 mt-1">Super Business Platform</p>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="lg:hidden p-1 rounded-md hover:bg-red-900/20"
            >
              <X className="h-5 w-5 text-red-300" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                data-testid={`nav-${item.name.toLowerCase().replace(' ', '-')}`}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group",
                    isActive
                      ? "bg-gradient-to-r from-red-900/40 to-amber-900/20 text-amber-200 border border-red-700/30 shadow-lg shadow-red-900/20"
                      : "text-gray-400 hover:bg-red-900/10 hover:text-red-200 border border-transparent"
                  )
                }
              >
                <item.icon className="h-5 w-5 group-[.active]:text-amber-400" />
                <span className="font-medium">{item.name}</span>
              </NavLink>
            ))}
          </nav>

          {/* User info */}
          <div className="p-4 border-t border-red-900/20 bg-red-950/20">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-red-600 to-amber-500 flex items-center justify-center text-white font-semibold shadow-lg shadow-red-900/30">
                AI
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-amber-100 truncate">OCB Business</p>
                <p className="text-xs text-red-300/50">Enterprise Plan</p>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;