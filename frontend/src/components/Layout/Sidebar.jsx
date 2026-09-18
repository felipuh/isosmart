import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Network, TrendingUp, Target, GitBranch, FileText, Settings, Award, FolderOpen, AlertTriangle, Users, Package, ClipboardList, Activity, LineChart, Zap, ShieldCheck } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const Sidebar = ({ isOpen = true, onClose }) => {
  const location = useLocation();
  const { t } = useI18n();
  
  const menuItems = [
    { name: t('navigation.dashboard'), path: '/', icon: Home, group: 'workspace' },
    { name: t('navigation.stakeholders'), path: '/stakeholders', icon: Network, group: 'clause4' },
    {
      name: t('navigation.context'),
      path: '/context',
      icon: TrendingUp,
      group: 'clause4',
      subItems: [
        { name: t('contextDashboard.tabs.overview'), path: '/context?tab=overview', tab: 'overview' },
        { name: t('contextDashboard.tabs.signals'), path: '/context?tab=signals', tab: 'signals' },
        { name: t('contextDashboard.tabs.alerts'), path: '/context?tab=alerts', tab: 'alerts' },
        { name: t('contextDashboard.tabs.radar'), path: '/context?tab=radar', tab: 'radar' },
      ],
    },
    { name: t('navigation.scope'), path: '/scope', icon: Target, group: 'clause4' },
    { name: t('navigation.processes'), path: '/processes', icon: GitBranch, group: 'clause4' },
    { name: t('navigation.documents'), path: '/documents', icon: FolderOpen, group: 'control' },
    { name: t('navigation.risks'), path: '/risks', icon: AlertTriangle, group: 'control' },
    { name: t('navigation.objectives'), path: '/objectives', icon: Award, group: 'control' },
    { name: t('navigation.planning'), path: '/planning', icon: ClipboardList, group: 'system' },
    { name: t('navigation.resources'), path: '/resources', icon: Package, group: 'system' },
    { name: t('navigation.operations'), path: '/operations', icon: Activity, group: 'system' },
    { name: t('navigation.improvement'), path: '/improvement', icon: Zap, group: 'assurance' },
    { name: t('navigation.performance'), path: '/performance', icon: LineChart, group: 'assurance' },
    { name: t('navigation.leadership'), path: '/leadership', icon: Users, group: 'assurance' },
    { name: t('navigation.reports'), path: '/reports', icon: FileText, group: 'workspace' },
    { name: t('navigation.settings'), path: '/settings', icon: Settings, group: 'workspace' },
  ];

  const groups = [
    { key: 'workspace', label: t('navigation.workspace', 'Workspace') },
    { key: 'clause4', label: t('navigation.contextAndScope', 'Context and scope') },
    { key: 'control', label: t('navigation.controlSystem', 'Governance controls') },
    { key: 'system', label: t('navigation.operatingSystem', 'Operating system') },
    { key: 'assurance', label: t('navigation.assurance', 'Assurance') },
  ];

  const currentTab = new URLSearchParams(location.search).get('tab') || 'overview';

  const isItemActive = (itemPath) => {
    if (itemPath === '/') {
      return location.pathname === '/';
    }
    return location.pathname === itemPath || location.pathname.startsWith(`${itemPath}/`);
  };

  return (
    <aside className={`fixed bottom-0 left-0 top-16 z-40 flex w-72 flex-col border-r border-slate-200 bg-white/95 text-slate-900 shadow-sm backdrop-blur transition-transform duration-300 dark:border-slate-800 dark:bg-slate-900/95 dark:text-white ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
      <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <div className="flex items-center gap-3 rounded-lg bg-slate-50 px-3 py-2.5 ring-1 ring-slate-200 dark:bg-slate-800/70 dark:ring-slate-700">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-800 text-white">
            <ShieldCheck className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-950 dark:text-white">{t('header.appTitle')}</p>
            <p className="truncate text-xs text-slate-500 dark:text-slate-400">{t('dashboard.main.standardsLine')}</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label={t('navigation.primary', 'Primary navigation')}>
        <div className="space-y-5">
          {groups.map((group) => {
            const items = menuItems.filter((item) => item.group === group.key);
            if (items.length === 0) return null;
            return (
              <div key={group.key}>
                <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
                  {group.label}
                </p>
                <ul className="space-y-1">
                  {items.map((item) => {
            const Icon = item.icon;
            const isActive = isItemActive(item.path);
            
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  onClick={onClose}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-800 ring-1 ring-blue-100 dark:bg-blue-950/40 dark:text-blue-100 dark:ring-blue-900/50'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
                  }`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="truncate">{item.name}</span>
                </Link>

                {item.subItems && (
                  <ul className="mt-1 ml-7 space-y-1 border-l border-slate-200 pl-2 dark:border-slate-800">
                    {item.subItems.map((subItem) => {
                      const subActive = location.pathname === '/context' && currentTab === subItem.tab;
                      return (
                        <li key={subItem.path}>
                          <Link
                            to={subItem.path}
                            onClick={onClose}
                            className={`block rounded-md px-3 py-2 text-sm transition-colors ${
                              subActive
                                ? 'bg-blue-50 text-blue-800 dark:bg-blue-950/40 dark:text-blue-100'
                                : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100'
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
              </div>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-200 p-4 dark:border-slate-800">
          <p className="text-center text-xs text-slate-500 dark:text-slate-400">
            {t('dashboard.main.standardsLine')}
          </p>
      </div>
    </aside>
  );
};

export default Sidebar;
