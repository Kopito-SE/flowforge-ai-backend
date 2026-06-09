import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Workflow,
  PlayCircle,
  Puzzle,
  Key,
  Users,
  FileText,
  Activity,
  Bell,
  Zap,
  BrainCircuit,
  Settings,
  ChevronDown,
  Menu,
  X,
  LayoutTemplate,
} from 'lucide-react';
import { useState } from 'react';
import { clsx } from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Workflows', href: '/workflows', icon: Workflow },
  { name: 'Templates', href: '/templates', icon: LayoutTemplate },
  { name: 'Executions', href: '/executions', icon: PlayCircle },
  { name: 'Events', href: '/events', icon: Zap },
  { name: 'Integrations', href: '/integrations', icon: Puzzle },
  { name: 'AI Playground', href: '/ai', icon: BrainCircuit },
  { name: 'API Keys', href: '/api-keys', icon: Key },
  { name: 'Organizations', href: '/organizations', icon: Users },
  { name: 'Audit Logs', href: '/audit-logs', icon: FileText },
  { name: 'Monitoring', href: '/monitoring', icon: Activity },
  { name: 'Alerts', href: '/alerts', icon: Bell },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="flex h-screen bg-surface-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-surface-200 flex flex-col transition-transform duration-200 lg:translate-x-0 lg:static lg:z-auto',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-surface-100">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <Workflow className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-surface-900">FlowForge</h1>
            <p className="text-xs text-surface-500">Automation Platform</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/');
            return (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={() => setSidebarOpen(false)}
                className={isActive ? 'sidebar-link-active' : 'sidebar-link-inactive'}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User info */}
        <div className="border-t border-surface-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <span className="text-sm font-semibold text-primary-700">AD</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-surface-900 truncate">Admin User</p>
              <p className="text-xs text-surface-500 truncate">admin@flowforge.io</p>
            </div>
            <ChevronDown className="w-4 h-4 text-surface-400" />
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="bg-white border-b border-surface-200 px-4 lg:px-6 py-3 flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 -ml-2 rounded-lg hover:bg-surface-100"
          >
            <Menu className="w-5 h-5 text-surface-600" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-2 h-2 bg-emerald-500 rounded-full absolute -top-0.5 -right-0.5" />
              <Bell className="w-5 h-5 text-surface-500 hover:text-surface-700 cursor-pointer" />
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}