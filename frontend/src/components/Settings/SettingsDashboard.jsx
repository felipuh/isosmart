import React, { useState, useEffect, useCallback } from 'react';
import { 
  Settings, Building2, Users, Brain, Bell, Database, 
  FileCheck, Palette, ChevronRight, Shield, Activity,
  Server, CreditCard
} from 'lucide-react';
import OrganizationSettings from './OrganizationSettings';
import UsersManagement from './UsersManagement';
import AIModulesSettings from './AIModulesSettings';
import NotificationSettings from './NotificationSettings';
import BackupExportSettings from './BackupExportSettings';
import ISOClausesSettings from './ISOClausesSettings';
import ThemeSettings from './ThemeSettings';
import BillingSettings from './BillingSettings';
import settingsService from '../../services/settingsService';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';

const SettingsDashboard = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const organizationId = currentOrganization?.id;
  const [activeTab, setActiveTab] = useState('organization');
  const [loading, setLoading] = useState(true);
  const [organization, setOrganization] = useState(null);
  const [settings, setSettings] = useState(null);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  const tabs = [
    { 
      id: 'organization', 
      label: t('settings.dashboard.tabs.organization.label'), 
      icon: Building2,
      description: t('settings.dashboard.tabs.organization.description')
    },
    { 
      id: 'users', 
      label: t('settings.dashboard.tabs.users.label'), 
      icon: Users,
      description: t('settings.dashboard.tabs.users.description')
    },
    { 
      id: 'ai-modules', 
      label: t('settings.dashboard.tabs.aiModules.label'), 
      icon: Brain,
      description: t('settings.dashboard.tabs.aiModules.description')
    },
    { 
      id: 'notifications', 
      label: t('settings.dashboard.tabs.notifications.label'), 
      icon: Bell,
      description: t('settings.dashboard.tabs.notifications.description')
    },
    {
      id: 'billing',
      label: t('settings.dashboard.tabs.billing.label'),
      icon: CreditCard,
      description: t('settings.dashboard.tabs.billing.description')
    },
    { 
      id: 'backup', 
      label: t('settings.dashboard.tabs.backup.label'), 
      icon: Database,
      description: t('settings.dashboard.tabs.backup.description')
    },
    { 
      id: 'iso', 
      label: t('settings.dashboard.tabs.iso.label'), 
      icon: FileCheck,
      description: t('settings.dashboard.tabs.iso.description')
    },
    { 
      id: 'theme', 
      label: t('settings.dashboard.tabs.theme.label'), 
      icon: Palette,
      description: t('settings.dashboard.tabs.theme.description')
    },
  ];

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [orgData, settingsData] = await Promise.all([
        settingsService.getOrganization(organizationId),
        settingsService.getSettings(organizationId)
      ]);
      
      setOrganization(orgData);
      setSettings(settingsData);
      
      // Cargar stats del dashboard
      try {
        const dashboardData = await settingsService.getOrganizationDashboard(organizationId);
        setStats(dashboardData);
      } catch {
        console.log('Dashboard stats not available');
      }
      
    } catch (err) {
      console.error('Error cargando configuración:', err);
      setError(t('settings.dashboard.messages.errorLoading'));
    } finally {
      setLoading(false);
    }
  }, [organizationId, t]);

  useEffect(() => {
    if (organizationId) {
      loadData();
    }
  }, [organizationId, loadData]);

  const handleSettingsUpdate = (newSettings) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  };

  const handleOrganizationUpdate = (newOrg) => {
    setOrganization(prev => ({ ...prev, ...newOrg }));
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'organization':
        return (
          <OrganizationSettings 
            organization={organization} 
            onUpdate={handleOrganizationUpdate}
          />
        );
      case 'users':
        return <UsersManagement />;
      case 'ai-modules':
        return (
          <AIModulesSettings 
            organizationId={organizationId}
            settings={settings} 
            onUpdate={handleSettingsUpdate}
          />
        );
      case 'notifications':
        return (
          <NotificationSettings 
            organizationId={organizationId}
            settings={settings} 
            onUpdate={handleSettingsUpdate}
          />
        );
      case 'billing':
        return (
          <BillingSettings
            organizationId={organizationId}
          />
        );
      case 'backup':
        return (
          <BackupExportSettings 
            organizationId={organizationId}
            settings={settings}
            onUpdate={handleSettingsUpdate}
          />
        );
      case 'iso':
        return <ISOClausesSettings />;
      case 'theme':
        return <ThemeSettings />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-12 bg-white/50 dark:bg-slate-800/50 rounded-xl w-1/3"></div>
            <div className="grid grid-cols-12 gap-6">
              <div className="col-span-3 h-96 bg-white/50 dark:bg-slate-800/50 rounded-2xl"></div>
              <div className="col-span-9 h-96 bg-white/50 dark:bg-slate-800/50 rounded-2xl"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 transition-colors duration-300">
      {/* Header */}
      <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border-b border-slate-200/50 dark:border-slate-700/50 sticky top-0 z-40">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/25">
                <Settings className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-300 bg-clip-text text-transparent">
                  {t('settings.title')}
                </h1>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {t('settings.dashboard.subtitle')}
                </p>
              </div>
            </div>
            
            {/* Quick Stats */}
            {stats && (
              <div className="hidden lg:flex items-center gap-6">
                <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 dark:bg-emerald-900/30 rounded-lg">
                  <Server className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
                    {t('settings.dashboard.stats.systemActive')}
                  </span>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                  <Users className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                    {t('settings.dashboard.stats.usersCount').replace('{count}', stats.users_count || 0)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl">
            <p className="text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-12 gap-6">
          {/* Sidebar Navigation */}
          <div className="col-span-12 lg:col-span-3">
            <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl rounded-2xl border border-slate-200/50 dark:border-slate-700/50 shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 overflow-hidden sticky top-24">
              <div className="p-4 border-b border-slate-200/50 dark:border-slate-700/50">
                <h2 className="font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  {t('settings.dashboard.sidebarTitle')}
                </h2>
              </div>
              
              <nav className="p-2">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      data-testid={`settings-tab-${tab.id}`}
                      className={`
                        w-full flex items-center gap-3 px-4 py-3 rounded-xl mb-1 transition-all duration-200
                        ${isActive 
                          ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg shadow-indigo-500/30' 
                          : 'hover:bg-slate-100 dark:hover:bg-slate-700/50 text-slate-600 dark:text-slate-300'
                        }
                      `}
                    >
                      <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                      <div className="flex-1 text-left">
                        <span className={`block font-medium ${isActive ? 'text-white' : ''}`}>
                          {tab.label}
                        </span>
                        <span className={`text-xs ${isActive ? 'text-indigo-100' : 'text-slate-400 dark:text-slate-500'}`}>
                          {tab.description}
                        </span>
                      </div>
                      <ChevronRight className={`w-4 h-4 transition-transform ${isActive ? 'translate-x-1' : ''}`} />
                    </button>
                  );
                })}
              </nav>

              {/* Organization Info Card */}
              {organization && (
                <div className="m-4 p-4 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-700/50 dark:to-slate-800/50 rounded-xl">
                  <div className="flex items-center gap-3 mb-3">
                    {organization.logo ? (
                      <img 
                        src={organization.logo} 
                        alt={organization.name}
                        className="w-10 h-10 rounded-lg object-cover"
                      />
                    ) : (
                      <div className="w-10 h-10 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-lg flex items-center justify-center">
                        <Building2 className="w-5 h-5 text-white" />
                      </div>
                    )}
                    <div>
                      <p className="font-semibold text-slate-800 dark:text-slate-200 text-sm">
                        {organization.name}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {t('settings.dashboard.organizationCard.planPrefix')} {organization.plan_type}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Activity className="w-3 h-3 text-emerald-500" />
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {organization.is_active
                        ? t('settings.dashboard.organizationCard.accountActive')
                        : t('settings.dashboard.organizationCard.accountInactive')}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Main Content */}
          <div className="col-span-12 lg:col-span-9">
            <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl rounded-2xl border border-slate-200/50 dark:border-slate-700/50 shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 overflow-hidden">
              {renderContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsDashboard;