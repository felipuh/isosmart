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
    { name: t('navigation.context'), path: '/context', icon: TrendingUp },
    { name: t('navigation.scope'), path: '/scope', icon: Target },
    { name: t('navigation.processes'), path: '/processes', icon: GitBranch },
    { name: t('navigation.documents'), path: '/documents', icon: FolderOpen },
    { name: t('navigation.risks'), path: '/risks', icon: AlertTriangle }, 
    { name: t('navigation.objectives'), path: '/objectives', icon: Award },
    { name: t('navigation.planning'), path: '/planning', icon: ClipboardList },
    { name: t('navigation.resources'), path: '/resources', icon: Package },
    { name: t('navigation.improvement'), path: '/improvement', icon: Zap },
    { name: t('navigation.performance'), path: '/performance', icon: LineChart },
    { name: t('navigation.leadership'), path: '/leadership', icon: Users },
    { name: t('navigation.settings'), path: '/settings', icon: Settings },
  ];

  return (
    <div className={`${isOpen ? 'w-64' : 'w-20'} bg-slate-900 dark:bg-slate-950 text-white flex flex-col transition-all duration-300 fixed left-0 top-16 bottom-0 z-40`}>
      {/* Menu Items */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
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
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      {isOpen && (
        <div className="p-4 border-t border-slate-800 dark:border-slate-800">
          <p className="text-xs text-slate-400 dark:text-slate-500 text-center">
            ISO 9001:2015 | ISO/IEC 42001:2023
          </p>
        </div>
      )}
    </div>
  );
};

export default Sidebar;
