import React from 'react';
import { Menu, Bell, Search, Moon, Sun } from 'lucide-react';
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

const Header = ({ sidebarOpen, setSidebarOpen }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

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
        
        <div className="hidden md:flex items-center gap-2 px-3 py-2 bg-red-950/30 backdrop-blur-sm rounded-lg border border-red-900/30">
          <Search className="h-4 w-4 text-red-400/60" />
          <input
            type="text"
            placeholder="Search..."
            className="bg-transparent border-none outline-none text-sm w-64 text-amber-50 placeholder:text-red-300/40"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
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