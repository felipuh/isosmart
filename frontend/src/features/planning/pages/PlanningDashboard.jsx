// features/planning/pages/PlanningDashboard.jsx
import React, { useCallback, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getRisksOpportunities,
  getObjectives,
  getActions,
  getChanges,
  getHighPriorityRisks,
  getAtRiskObjectives,
  getOverdueActions,
  getPendingChanges,
  getPlanningCockpitKPIs
} from '../api/planningApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const PlanningDashboard = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const statColors = {
    red: {
      card: 'from-red-500/10 to-red-600/5 border-red-500/20 hover:shadow-red-500/20',
      value: 'text-red-600 dark:text-red-400'
    },
    green: {
      card: 'from-green-500/10 to-green-600/5 border-green-500/20 hover:shadow-green-500/20',
      value: 'text-green-600 dark:text-green-400'
    },
    blue: {
      card: 'from-blue-500/10 to-blue-600/5 border-blue-500/20 hover:shadow-blue-500/20',
      value: 'text-blue-600 dark:text-blue-400'
    },
    purple: {
      card: 'from-purple-500/10 to-purple-600/5 border-purple-500/20 hover:shadow-purple-500/20',
      value: 'text-purple-600 dark:text-purple-400'
    }
  };

  const [stats, setStats] = useState({
    risks: { total: 0, high: 0 },
    opportunities: { total: 0 },
    objectives: { total: 0, active: 0, at_risk: 0 },
    actions: { total: 0, overdue: 0 },
    changes: { total: 0, pending: 0 }
  });
  const [cockpit, setCockpit] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);

      const [
        risksData,
        objectivesData,
        actionsData,
        changesData,
        highRisks,
        atRiskObjs,
        overdueActs,
        pendingChgs,
        cockpitData
      ] = await Promise.all([
        getRisksOpportunities({ organization_id: orgId }),
        getObjectives({ organization_id: orgId }),
        getActions({ organization_id: orgId }),
        getChanges({ organization_id: orgId }),
        getHighPriorityRisks(orgId),
        getAtRiskObjectives(orgId),
        getOverdueActions(orgId),
        getPendingChanges(orgId),
        getPlanningCockpitKPIs(orgId)
      ]);

      const risks = normalizeList(risksData);
      const objectives = normalizeList(objectivesData);
      const actions = normalizeList(actionsData);
      const changes = normalizeList(changesData);
      setCockpit(cockpitData);

      setStats({
        risks: {
          total: risks.filter(r => r.item_type === 'risk').length,
          high: normalizeList(highRisks).length
        },
        opportunities: {
          total: risks.filter(r => r.item_type === 'opportunity').length
        },
        objectives: {
          total: objectives.length,
          active: objectives.filter(o => o.status === 'in_progress').length,
          at_risk: normalizeList(atRiskObjs).length
        },
        actions: {
          total: actions.length,
          overdue: normalizeList(overdueActs).length
        },
        changes: {
          total: changes.length,
          pending: normalizeList(pendingChgs).length
        }
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    if (orgId) loadDashboardData();
  }, [orgId, loadDashboardData]);

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
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{t('modules.planning.dashboard.title')}</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">{t('modules.planning.dashboard.subtitle')}</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title={t('modules.planning.dashboard.stats.risks')}
          value={stats.risks.total}
          subtitle={t('modules.planning.dashboard.stats.risksDetail').replace('{count}', stats.risks.high)}
          icon="⚠️"
          link="/planning/risks-opportunities"
          color="red"
        />

        <StatCard
          title={t('modules.planning.dashboard.stats.opportunities')}
          value={stats.opportunities.total}
          subtitle={t('modules.planning.dashboard.stats.opportunitiesDetail')}
          icon="🎯"
          link="/planning/risks-opportunities"
          color="green"
        />

        <StatCard
          title={t('modules.planning.dashboard.stats.objectives')}
          value={stats.objectives.total}
          subtitle={t('modules.planning.dashboard.stats.objectivesDetail')
            .replace('{active}', stats.objectives.active)
            .replace('{atRisk}', stats.objectives.at_risk)}
          icon="🎪"
          link="/planning/objectives"
          color="blue"
        />

        <StatCard
          title={t('modules.planning.dashboard.stats.actions')}
          value={stats.actions.total}
          subtitle={t('modules.planning.dashboard.stats.actionsDetail').replace('{count}', stats.actions.overdue)}
          icon="✅"
          link="/planning/actions"
          color="purple"
        />
      </div>

      {cockpit?.alerts?.length > 0 && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-amber-800 dark:text-amber-200 mb-2">{t('modules.planning.dashboard.alertsTitle')}</h3>
          <ul className="space-y-1">
            {cockpit.alerts.map((alert, index) => (
              <li key={index} className="text-xs text-amber-700 dark:text-amber-300">• {alert.message}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Change Control */}
      <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-500/20 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-orange-800 dark:text-orange-100">{t('modules.planning.dashboard.changeControl.title')}</h2>
            <p className="text-sm text-orange-700 dark:text-orange-200">{t('modules.planning.dashboard.changeControl.subtitle')}</p>
          </div>
          <Link
            to="/planning/changes"
            className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-all"
          >
            {t('modules.planning.dashboard.changeControl.viewAll')}
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/70 dark:bg-slate-800/40 rounded-lg p-4">
            <p className="text-2xl font-bold text-orange-400">{stats.changes.total}</p>
            <p className="text-sm text-slate-600 dark:text-slate-400">{t('modules.planning.dashboard.changeControl.totalChanges')}</p>
          </div>
          <div className="bg-white/70 dark:bg-slate-800/40 rounded-lg p-4">
            <p className="text-2xl font-bold text-yellow-400">{stats.changes.pending}</p>
            <p className="text-sm text-slate-600 dark:text-slate-400">{t('modules.planning.dashboard.changeControl.pendingApproval')}</p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6 shadow dark:shadow-slate-900/50">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">{t('modules.planning.dashboard.quickActions.title')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/planning/risks-opportunities/new"
            className="flex items-center space-x-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-all"
          >
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.planning.dashboard.quickActions.newRiskOpportunity')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.planning.dashboard.quickActions.identifyAndAssess')}</p>
            </div>
          </Link>

          <Link
            to="/planning/objectives/new"
            className="flex items-center space-x-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all"
          >
            <span className="text-2xl">🎯</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.planning.dashboard.quickActions.newObjective')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.planning.dashboard.quickActions.createSmartObjective')}</p>
            </div>
          </Link>

          <Link
            to="/planning/changes/new"
            className="flex items-center space-x-3 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg hover:bg-orange-500/20 transition-all"
          >
            <span className="text-2xl">🔄</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.planning.dashboard.quickActions.requestChange')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.planning.dashboard.quickActions.changeControlQms')}</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default PlanningDashboard;