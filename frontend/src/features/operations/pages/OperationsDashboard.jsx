// features/operations/pages/OperationsDashboard.jsx
import React, { useCallback, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getCustomerRequirements,
  getDesignProjects,
  getExternalProviders,
  getNonconformities,
  getProductReleases,
  getPendingReviewRequirements,
  getOpenNonconformities,
  getCriticalNonconformities,
  getOperationsCockpitKpis,
  analyzeOperationsRequirementsAI,
  analyzeOperationsProvidersAI,
  analyzeOperationsReleasesAI,
  analyzeOperationsNonconformitiesAI,
} from '../api/operationsApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const OperationsDashboard = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const statColors = {
    blue: {
      card: 'from-blue-500/10 to-blue-600/5 border-blue-500/20 hover:shadow-blue-500/20',
      value: 'text-blue-600 dark:text-blue-400'
    },
    purple: {
      card: 'from-purple-500/10 to-purple-600/5 border-purple-500/20 hover:shadow-purple-500/20',
      value: 'text-purple-600 dark:text-purple-400'
    },
    green: {
      card: 'from-green-500/10 to-green-600/5 border-green-500/20 hover:shadow-green-500/20',
      value: 'text-green-600 dark:text-green-400'
    },
    red: {
      card: 'from-red-500/10 to-red-600/5 border-red-500/20 hover:shadow-red-500/20',
      value: 'text-red-600 dark:text-red-400'
    }
  };

  const [stats, setStats] = useState({
    requirements: { total: 0, pending_review: 0 },
    design_projects: { total: 0, active: 0 },
    providers: { total: 0, approved: 0 },
    releases: { total: 0, pending: 0 },
    nonconformities: { total: 0, open: 0, critical: 0 }
  });
  const [loading, setLoading] = useState(true);
  const [cockpit, setCockpit] = useState(null);
  const [aiInsights, setAiInsights] = useState({
    requirements: null,
    providers: null,
    releases: null,
    nonconformities: null,
  });

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);

      const [
        requirementsData,
        designData,
        providersData,
        releasesData,
        ncsData,
        pendingReqs,
        openNCs,
        criticalNCs,
        cockpitData
      ] = await Promise.all([
        getCustomerRequirements({ organization_id: orgId }),
        getDesignProjects({ organization_id: orgId }),
        getExternalProviders({ organization_id: orgId }),
        getProductReleases({ organization_id: orgId }),
        getNonconformities({ organization_id: orgId }),
        getPendingReviewRequirements(orgId),
        getOpenNonconformities(orgId),
        getCriticalNonconformities(orgId),
        getOperationsCockpitKpis(orgId).catch(() => null)
      ]);

      const requirements = normalizeList(requirementsData);
      const design = normalizeList(designData);
      const providers = normalizeList(providersData);
      const releases = normalizeList(releasesData);
      const ncs = normalizeList(ncsData);

      setStats({
        requirements: {
          total: requirements.length,
          pending_review: normalizeList(pendingReqs).length
        },
        design_projects: {
          total: design.length,
          active: design.filter(p => p.status === 'active').length
        },
        providers: {
          total: providers.length,
          approved: providers.filter(p => p.classification === 'approved').length
        },
        releases: {
          total: releases.length,
          pending: releases.filter(r => r.status === 'pending').length
        },
        nonconformities: {
          total: ncs.length,
          open: normalizeList(openNCs).length,
          critical: normalizeList(criticalNCs).length
        }
      });
      setCockpit(cockpitData);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    if (orgId) loadDashboardData();
  }, [orgId, loadDashboardData]);

  const runAiInsight = async (kind) => {
    if (!orgId) return;
    try {
      const actionMap = {
        requirements: analyzeOperationsRequirementsAI,
        providers: analyzeOperationsProvidersAI,
        releases: analyzeOperationsReleasesAI,
        nonconformities: analyzeOperationsNonconformitiesAI,
      };
      const executor = actionMap[kind];
      if (!executor) return;
      const result = await executor(orgId);
      setAiInsights(prev => ({ ...prev, [kind]: result }));
    } catch (error) {
      console.error('Error generating operations AI insight:', error);
    }
  };

  const StatCard = ({ title, value, subtitle, icon, link, color = 'blue' }) => {
    const palette = statColors[color] || statColors.blue;
    return (
      <Link to={link} className="block">
        <div className={`bg-gradient-to-br ${palette.card} border rounded-lg p-6 hover:shadow-lg transition-all duration-300 bg-white dark:bg-slate-800 shadow dark:shadow-slate-900/50 border-slate-200 dark:border-slate-700`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-slate-600 dark:text-slate-300">{title}</h3>
            <span className="text-2xl">{icon}</span>
          </div>
          <div className="flex items-baseline">
            <p className={`text-3xl font-bold ${palette.value}`}>{value}</p>
          </div>
          {subtitle && <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">{subtitle}</p>}
        </div>
      </Link>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen transition-colors duration-300 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{t('modules.operations.dashboard.title')}</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">{t('modules.operations.dashboard.subtitle')}</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title={t('modules.operations.dashboard.stats.customerRequirements.title')}
          value={stats.requirements.total}
          subtitle={`${stats.requirements.pending_review} ${t('modules.operations.dashboard.stats.customerRequirements.pendingReviewSuffix')}`}
          icon="📋"
          link="/operations/requirements"
          color="blue"
        />

        <StatCard
          title={t('modules.operations.dashboard.stats.designProjects.title')}
          value={stats.design_projects.total}
          subtitle={`${stats.design_projects.active} ${t('modules.operations.dashboard.stats.designProjects.activeSuffix')}`}
          icon="🎨"
          link="/operations/design-projects"
          color="purple"
        />

        <StatCard
          title={t('modules.operations.dashboard.stats.externalProviders.title')}
          value={stats.providers.total}
          subtitle={`${stats.providers.approved} ${t('modules.operations.dashboard.stats.externalProviders.approvedSuffix')}`}
          icon="🏢"
          link="/operations/providers"
          color="green"
        />

        <StatCard
          title={t('modules.operations.dashboard.stats.nonconformities.title')}
          value={stats.nonconformities.total}
          subtitle={`${stats.nonconformities.open} ${t('modules.operations.dashboard.stats.nonconformities.openSuffix')}, ${stats.nonconformities.critical} ${t('modules.operations.dashboard.stats.nonconformities.criticalSuffix')}`}
          icon="⚠️"
          link="/operations/nonconformities"
          color="red"
        />
      </div>

      {/* Alerts Section */}
      {stats.nonconformities.critical > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-500/20 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">🚨</span>
            <h2 className="text-xl font-bold text-red-800 dark:text-red-100">{t('modules.operations.dashboard.alerts.title')}</h2>
          </div>
          <p className="text-red-700 dark:text-red-200">
            {t('modules.operations.dashboard.alerts.messagePrefix')} {stats.nonconformities.critical} {t('modules.operations.dashboard.alerts.messageSuffix')}
          </p>
          <Link
            to="/operations/nonconformities"
            className="inline-block mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all"
          >
            {t('modules.operations.dashboard.alerts.viewCritical')}
          </Link>
        </div>
      )}

      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6 shadow dark:shadow-slate-900/50">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">{t('modules.operations.dashboard.cockpit.title')}</h2>
          <span className="text-xs px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200">
            {cockpit?.ai?.risk_level || 'n/a'}
          </span>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
          {t('modules.operations.dashboard.cockpit.subtitle')}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          {(cockpit?.ai?.alerts || []).map((alert, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-200 text-sm">
              {alert}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button type="button" onClick={() => runAiInsight('requirements')} className="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition-all">{t('modules.operations.dashboard.cockpit.actions.requirements')}</button>
          <button type="button" onClick={() => runAiInsight('providers')} className="px-3 py-2 rounded-lg bg-emerald-600 text-white text-sm hover:bg-emerald-700 transition-all">{t('modules.operations.dashboard.cockpit.actions.providers')}</button>
          <button type="button" onClick={() => runAiInsight('releases')} className="px-3 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-700 transition-all">{t('modules.operations.dashboard.cockpit.actions.releases')}</button>
          <button type="button" onClick={() => runAiInsight('nonconformities')} className="px-3 py-2 rounded-lg bg-rose-600 text-white text-sm hover:bg-rose-700 transition-all">{t('modules.operations.dashboard.cockpit.actions.nonconformities')}</button>
        </div>
        {(aiInsights.requirements || aiInsights.providers || aiInsights.releases || aiInsights.nonconformities) && (
          <div className="mt-4 p-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 text-sm text-slate-700 dark:text-slate-200 space-y-2">
            {aiInsights.requirements?.summary && <p>{t('modules.operations.dashboard.cockpit.summary.requirements').replace('{count}', aiInsights.requirements.summary.pending_review || 0)}</p>}
            {aiInsights.providers?.top_risks?.length > 0 && <p>{t('modules.operations.dashboard.cockpit.summary.providers').replace('{count}', aiInsights.providers.top_risks.length)}</p>}
            {aiInsights.releases?.recommendations && <p>{t('modules.operations.dashboard.cockpit.summary.releases').replace('{count}', aiInsights.releases.recommendations.filter(r => r.decision === 'hold').length)}</p>}
            {aiInsights.nonconformities?.items && <p>{t('modules.operations.dashboard.cockpit.summary.nonconformities').replace('{count}', aiInsights.nonconformities.items.length)}</p>}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6 shadow dark:shadow-slate-900/50">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">{t('modules.operations.dashboard.quickActions.title')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/operations/requirements/new"
            className="flex items-center space-x-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all"
          >
            <span className="text-2xl">📋</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.operations.dashboard.quickActions.newRequirement')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.operations.dashboard.quickActions.newRequirementDesc')}</p>
            </div>
          </Link>

          <Link
            to="/operations/nonconformities/new"
            className="flex items-center space-x-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-all"
          >
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.operations.dashboard.quickActions.reportNc')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.operations.dashboard.quickActions.reportNcDesc')}</p>
            </div>
          </Link>

          <Link
            to="/operations/releases/new"
            className="flex items-center space-x-3 p-4 bg-green-500/10 border border-green-500/20 rounded-lg hover:bg-green-500/20 transition-all"
          >
            <span className="text-2xl">✅</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.operations.dashboard.quickActions.releaseProduct')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.operations.dashboard.quickActions.releaseProductDesc')}</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Module Links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          to="/operations/releases"
          className="p-6 bg-gradient-to-br from-green-500/10 to-green-600/5 border border-green-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">📦</span>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">{t('modules.operations.dashboard.moduleLinks.releasesTitle')}</h3>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {stats.releases.pending} {t('modules.operations.dashboard.moduleLinks.pendingReleasesSuffix')}
          </p>
        </Link>

        <Link
          to="/operations/production"
          className="p-6 bg-gradient-to-br from-orange-500/10 to-orange-600/5 border border-orange-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">⚙️</span>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">{t('modules.operations.dashboard.moduleLinks.productionTitle')}</h3>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">{t('modules.operations.dashboard.moduleLinks.productionSubtitle')}</p>
        </Link>
      </div>
    </div>
  );
};

export default OperationsDashboard;