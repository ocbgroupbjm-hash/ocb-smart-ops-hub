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
          "fixed lg:static inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transform transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
                AI BOS
              </h1>
              <p className="text-xs text-muted-foreground mt-1">Business Operating System</p>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="lg:hidden p-1 rounded-md hover:bg-accent"
            >
              <X className="h-5 w-5" />
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
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )
                }
              >
                <item.icon className="h-5 w-5" />
                <span className="font-medium">{item.name}</span>
              </NavLink>
            ))}
          </nav>

          {/* User info */}
          <div className="p-4 border-t border-border">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-semibold">
                AI
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">AI Business</p>
                <p className="text-xs text-muted-foreground">Starter Plan</p>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;