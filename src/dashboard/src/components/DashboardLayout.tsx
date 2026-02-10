import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  LayoutDashboard,
  FileText,
  FileCheck,
  Search,
  ArrowRightLeft,
  LogOut,
  Menu,
  X,
  Shield,
  ChevronRight,
} from 'lucide-react';
import { cn } from '../lib/utils';

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/' },
  { label: 'SOP Assistant', icon: FileText, path: '/sop' },
  { label: 'Chargesheet Review', icon: FileCheck, path: '/chargesheet' },
  { label: 'Case Search', icon: Search, path: '/search' },
  { label: 'Section Converter', icon: ArrowRightLeft, path: '/tools/sections' },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const currentNav = navItems.find((n) => n.path === location.pathname) || navItems[0];

  return (
    <div className="min-h-screen bg-surface-0 bg-mesh noise flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:sticky top-0 left-0 z-50 h-screen w-72 flex flex-col',
          'bg-surface-1/80 backdrop-blur-xl border-r border-white/[0.04]',
          'transition-transform duration-300 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="p-6 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl gradient-gold flex items-center justify-center shadow-lg shadow-gold-500/20">
            <Shield className="w-5 h-5 text-surface-0" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="font-display font-bold text-sm tracking-wide text-white">
              Gujarat Police
            </h1>
            <p className="text-[10px] uppercase tracking-[0.2em] text-gold-500/70 font-medium">
              AI Investigation
            </p>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1.5 rounded-lg hover:bg-white/5 text-white/40"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const active = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  'group flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200',
                  active
                    ? 'bg-gold-500/10 text-gold-400 border border-gold-500/15'
                    : 'text-white/50 hover:text-white/80 hover:bg-white/[0.03]'
                )}
              >
                <item.icon
                  className={cn(
                    'w-[18px] h-[18px] flex-shrink-0 transition-colors',
                    active ? 'text-gold-500' : 'text-white/30 group-hover:text-white/50'
                  )}
                />
                <span className="flex-1">{item.label}</span>
                {active && (
                  <ChevronRight className="w-4 h-4 text-gold-500/50" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* User */}
        <div className="p-4 border-t border-white/[0.04]">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-lg bg-navy-700 flex items-center justify-center text-xs font-bold text-gold-400 uppercase">
              {user?.username?.[0] || 'A'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white/80 truncate">
                {user?.username || 'Officer'}
              </p>
              <p className="text-xs text-white/30">{user?.role || 'Admin'}</p>
            </div>
            <button
              onClick={logout}
              className="p-2 rounded-lg hover:bg-red-500/10 text-white/30 hover:text-red-400 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 min-h-screen flex flex-col">
        {/* Top bar */}
        <header className="sticky top-0 z-30 h-16 flex items-center gap-4 px-6 bg-surface-0/60 backdrop-blur-xl border-b border-white/[0.04]">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 -ml-2 rounded-lg hover:bg-white/5 text-white/50"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2 text-sm">
            <span className="text-white/30">Gujarat Police AI</span>
            <ChevronRight className="w-3.5 h-3.5 text-white/15" />
            <span className="text-white/70 font-medium">{currentNav.label}</span>
          </div>

          <div className="ml-auto flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-medium text-emerald-400">System Online</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
