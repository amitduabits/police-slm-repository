import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  FileText,
  Search,
  Shield,
  FileCheck,
  Settings,
  LogOut,
} from 'lucide-react';
import { clearTokens } from '../lib/api';

interface DashboardLayoutProps {
  children: ReactNode;
  onLogout: () => void;
}

const navItems = [
  { path: '/', icon: Home, label: 'Dashboard' },
  { path: '/sop', icon: FileText, label: 'SOP Assistant' },
  { path: '/chargesheet', icon: FileCheck, label: 'Chargesheet Review' },
  { path: '/search', icon: Search, label: 'Case Search' },
  { path: '/tools/sections', icon: Settings, label: 'Section Converter' },
];

export default function DashboardLayout({ children, onLogout }: DashboardLayoutProps) {
  const location = useLocation();

  const handleLogout = () => {
    clearTokens();
    onLogout();
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-[#1B3A5C] text-white flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-[#2A4A6C]">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-[#D4AF37]" />
            <div>
              <h1 className="font-bold text-lg">Gujarat Police</h1>
              <p className="text-xs text-gray-300">AI Support System</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-[#2A4A6C] text-white'
                    : 'text-gray-300 hover:bg-[#2A4A6C] hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-[#2A4A6C]">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 w-full text-gray-300 hover:bg-[#2A4A6C] hover:text-white rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="container mx-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
