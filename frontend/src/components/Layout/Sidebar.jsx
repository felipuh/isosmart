import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Network, TrendingUp, Target, GitBranch, FileText, Settings, Award, FolderOpen, AlertTriangle, Users, Package, ClipboardList, Activity, LineChart, Zap } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const Sidebar = ({ isOpen = true }) => {
  const location = useLocation();
  const { t } = useI18n();
  
  const menuItems = [
    { name: t('navigation.dashboard'), path: '/', icon: Home },
    { name: t('navigation.stakeholders'), path: '/stakeholders', icon: Network },
    {
      name: t('navigation.context'),
      path: '/context',
      icon: TrendingUp,
      subItems: [
        { name: t('contextDashboard.tabs.overview'), path: '/context?tab=overview', tab: 'overview' },
        { name: t('contextDashboard.tabs.signals'), path: '/context?tab=signals', tab: 'signals' },
        { name: t('contextDashboard.tabs.alerts'), path: '/context?tab=alerts', tab: 'alerts' },
        { name: t('contextDashboard.tabs.radar'), path: '/context?tab=radar', tab: 'radar' },
      ],
    },
    { name: t('navigation.scope'), path: '/scope', icon: Target },
    { name: t('navigation.processes'), path: '/processes', icon: GitBranch },
    { name: t('navigation.documents'), path: '/documents', icon: FolderOpen },
    { name: t('navigation.risks'), path: '/risks', icon: AlertTriangle }, 
    { name: t('navigation.objectives'), path: '/objectives', icon: Award },
    { name: t('navigation.planning'), path: '/planning', icon: ClipboardList },
    { name: t('navigation.resources'), path: '/resources', icon: Package },
    { name: t('navigation.operations'), path: '/operations', icon: Activity },
    { name: t('navigation.improvement'), path: '/improvement', icon: Zap },
    { name: t('navigation.performance'), path: '/performance', icon: LineChart },
    { name: t('navigation.leadership'), path: '/leadership', icon: Users },
    { name: t('navigation.reports'), path: '/reports', icon: FileText },
    { name: t('navigation.settings'), path: '/settings', icon: Settings },
  ];

  const currentTab = new URLSearchParams(location.search).get('tab') || 'overview';

  const isItemActive = (itemPath) => {
    if (itemPath === '/') {
      return location.pathname === '/';
    }
    return location.pathname === itemPath || location.pathname.startsWith(`${itemPath}/`);
  };

  return (
    <div className={`${isOpen ? 'w-64' : 'w-20'} bg-slate-900 dark:bg-slate-950 text-white flex flex-col transition-all duration-300 fixed left-0 top-16 bottom-0 z-40`}>
      {/* Menu Items */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = isItemActive(item.path);
            
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`flex items-center ${isOpen ? 'space-x-3 px-4' : 'justify-center px-2'} py-3 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25'
                      : 'text-slate-300 dark:text-slate-400 hover:bg-slate-800 dark:hover:bg-slate-800 hover:text-white'
                  }`}
                  title={!isOpen ? item.name : ''}
                >
                  <Icon className="h-5 w-5" />
                  {isOpen && <span>{item.name}</span>}
                </Link>

                {isOpen && item.subItems && (
                  <ul className="mt-1 ml-7 space-y-1">
                    {item.subItems.map((subItem) => {
                      const subActive = location.pathname === '/context' && currentTab === subItem.tab;
                      return (
                        <li key={subItem.path}>
                          <Link
                            to={subItem.path}
                            className={`block rounded-md px-3 py-2 text-sm transition-colors ${
                              subActive
                                ? 'bg-blue-900/40 text-blue-200'
                                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                            }`}
                          >
                            {subItem.name}
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      {isOpen && (
        <div className="p-4 border-t border-slate-800 dark:border-slate-800">
          <p className="text-xs text-slate-400 dark:text-slate-500 text-center">
            {t('dashboard.main.standardsLine')}
          </p>
        </div>
      )}
    </div>
  );
};

export default Sidebar;