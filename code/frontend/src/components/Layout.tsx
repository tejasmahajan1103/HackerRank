import type { ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Wallet, MessageSquare, Calculator, TrendingUp, CreditCard, Settings, LayoutDashboard } from 'lucide-react';
import type { Location } from 'react-router-dom';

const navigation: Array<{ name: string; href: string; icon: React.ComponentType<{ className?: string }> }> = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'AI Chat', href: '/chat', icon: MessageSquare },
  { name: 'Analyze', href: '/analyze', icon: Calculator },
  { name: 'Forecast', href: '/forecast', icon: TrendingUp },
  { name: 'Transactions', href: '/transactions', icon: CreditCard },
  { name: 'Plans', href: '/plans', icon: Wallet },
  { name: 'Profile', href: '/profile', icon: Settings },
];

export function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      <Sidebar navigation={navigation} location={location} />
      <div className="flex-1 flex flex-col min-w-0 ml-64">
        <Header location={location} />
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

function Sidebar({ navigation, location }: { navigation: NavItem[]; location: Location }) {
  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col z-10">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Wallet className="w-6 h-6 text-green-600" />
          Buy or Wait
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Financial Decision Agent</p>
      </div>
      
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navigation.map((item: NavItem) => {
          const isActive = location.pathname === item.href || 
            (item.href !== '/' && location.pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {item.name}
            </NavLink>
          );
        })}
      </nav>
      
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="text-xs text-gray-500 dark:text-gray-400">
          v1.0.0 | HackerRank Submission
        </div>
      </div>
    </aside>
  );
}

function Header({ location }: { location: Location }) {
  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {getPageTitle(location.pathname)}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {getPageDescription(location.pathname)}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 dark:bg-green-900/30 rounded-full">
            <span className="w-2 h-2 bg-green-500 rounded-full" />
            <span className="text-sm font-medium text-green-700 dark:text-green-300">API Connected</span>
          </div>
        </div>
      </div>
    </header>
  );
}

function getPageTitle(pathname: string): string {
  const titles: Record<string, string> = {
    '/': 'Dashboard',
    '/chat': 'AI Chat',
    '/analyze': 'Analyze',
    '/forecast': 'Forecast',
    '/transactions': 'Transactions',
    '/plans': 'Plans',
    '/profile': 'Profile',
  };
  return titles[pathname] || 'Dashboard';
}

function getPageDescription(pathname: string): string {
  const descriptions: Record<string, string> = {
    '/': 'Your financial overview and insights',
    '/chat': 'Chat with your AI financial assistant',
    '/analyze': 'Analyze affordability of expenses',
    '/forecast': '90-day cash flow projection',
    '/transactions': 'View and filter transactions',
    '/plans': 'Compare payment plan options',
    '/profile': 'Manage your profile settings',
  };
  return descriptions[pathname] || 'Your financial overview and insights';
}