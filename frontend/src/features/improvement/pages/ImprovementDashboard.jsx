import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getNonconformities, getNonconformityStats,
  getCorrectiveActions, getOverdueActions,
  getContinualImprovements, getActiveInitiatives,
  getImprovementCockpitKpis,
  analyzeImprovementRootCauseAI,
  analyzeCorrectiveTrackerAI,
  analyzeContinualOptimizerAI,
} from '../api/improvementApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const statColors = {
  red:    { card: 'from-red-500/10 to-red-600/5 border-red-500/20', value: 'text-red-600 dark:text-red-400', shadow: 'shadow-red-500/10' },
  orange: { card: 'from-orange-500/10 to-orange-600/5 border-orange-500/20', value: 'text-orange-600 dark:text-orange-400', shadow: 'shadow-orange-500/10' },
  blue:   { card: 'from-blue-500/10 to-blue-600/5 border-blue-500/20', value: 'text-blue-600 dark:text-blue-400', shadow: 'shadow-blue-500/10' },
  green:  { card: 'from-green-500/10 to-green-600/5 border-green-500/20', value: 'text-green-600 dark:text-green-400', shadow: 'shadow-green-500/10' },
};

const ImprovementDashboard = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const [loading, setLoading] = useState(true);
  const [cockpit, setCockpit] = useState(null);
  const [aiInsights, setAiInsights] = useState({
    rootCause: null,
    tracker: null,
    optimizer: null,
  });
  const [stats, setStats] = useState({
    nonconformities: { total: 0, open: 0, closed: 0, critical: 0 },
    corrective_actions: { total: 0, overdue: 0, effective: 0 },
    improvements: { total: 0, active: 0, successful: 0 }
  });

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const [ncsData, ncStats, actionsData, overdueData, improvementsData, activeData, cockpitData] = await Promise.all([
        getNonconformities({ organization_id: orgId }),
        getNonconformityStats(orgId).catch(() => null),
        getCorrectiveActions({ organization_id: orgId }),
        getOverdueActions(orgId).catch(() => []),
        getContinualImprovements({ organization_id: orgId }),
        getActiveInitiatives(orgId).catch(() => []),
        getImprovementCockpitKpis(orgId).catch(() => null)
      ]);

      const ncs = normalizeList(ncsData);
      const actions = normalizeList(actionsData);
      const overdue = normalizeList(overdueData);
      const improvements = normalizeList(improvementsData);
      const active = normalizeList(activeData);

      setStats({
        nonconformities: {
          total: ncStats?.total ?? ncs.length,
          open: ncStats?.open ?? ncs.filter(n => n.status === 'open').length,
          closed: ncStats?.closed ?? ncs.filter(n => n.status === 'closed').length,
          critical: ncStats?.critical ?? ncs.filter(n => n.severity === 'critical').length,
        },
        corrective_actions: {
          total: actions.length,
          overdue: overdue.length,
          effective: actions.filter(a => a.is_effective === true).length,
        },
        improvements: {
          total: improvements.length,
          active: active.length,
          successful: improvements.filter(i => i.status === 'successful').length,
        }
      });
      setCockpit(cockpitData);
    } catch (error) {
      console.error('Error loading improvement dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => { if (orgId) loadDashboard(); }, [orgId, loadDashboard]);

  const runAiInsight = async (kind) => {
    if (!orgId) return;
    try {
      const actionMap = {
        rootCause: analyzeImprovementRootCauseAI,
        tracker: analyzeCorrectiveTrackerAI,
        optimizer: analyzeContinualOptimizerAI,
      };
      const executor = actionMap[kind];
      if (!executor) return;
      const result = await executor(orgId);
      setAiInsights(prev => ({ ...prev, [kind]: result }));
    } catch (error) {
      console.error('Error generating improvement AI insight:', error);
    }
  };

  const StatCard = ({ title, value, subtitle, icon, link, color = 'blue' }) => {
    const palette = statColors[color] || statColors.blue;
    return (
      <Link to={link} className="block">
        <div className={`bg-gradient-to-br ${palette.card} border rounded-lg p-6 hover:shadow-lg ${palette.shadow} transition-all duration-300 bg-white dark:bg-slate-800 shadow dark:shadow-slate-900/50 border-slate-200 dark:border-slate-700`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-slate-600 dark:text-slate-300">{title}</h3>
            <span className="text-2xl">{icon}</span>
          </div>
          <p className={`text-3xl font-bold ${palette.value}`}>{value}</p>
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
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{t('modules.improvement.dashboard.title')}</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">{t('modules.improvement.dashboard.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title={t('modules.improvement.dashboard.stats.nonconformities')} value={stats.nonconformities.total}
          subtitle={t('modules.improvement.dashboard.stats.nonconformitiesDetail').replace('{open}', stats.nonconformities.open).replace('{critical}', stats.nonconformities.critical)}
          icon="🚨" link="/improvement/nonconformities" color="red" />
        <StatCard title={t('modules.improvement.dashboard.stats.correctiveActions')} value={stats.corrective_actions.total}
          subtitle={t('modules.improvement.dashboard.stats.actionsDetail').replace('{overdue}', stats.corrective_actions.overdue).replace('{effective}', stats.corrective_actions.effective)}
          icon="🔧" link="/improvement/corrective-actions" color="orange" />
        <StatCard title={t('modules.improvement.dashboard.stats.continualImprovement')} value={stats.improvements.total}
          subtitle={t('modules.improvement.dashboard.stats.improvementsDetail').replace('{active}', stats.improvements.active).replace('{successful}', stats.improvements.successful)}
          icon="📈" link="/improvement/continual" color="green" />
        <StatCard title={t('modules.improvement.dashboard.stats.effectiveness')}
          value={stats.corrective_actions.total > 0 ? `${Math.round((stats.corrective_actions.effective / stats.corrective_actions.total) * 100)}%` : t('modules.improvement.dashboard.stats.notAvailable')}
          subtitle={t('modules.improvement.dashboard.stats.effectivenessDetail')} icon="✅" link="/improvement/corrective-actions" color="blue" />
      </div>

      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6 shadow dark:shadow-slate-900/50">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">{t('modules.improvement.dashboard.cockpit.title')}</h2>
          <span className="text-xs px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200">
            {cockpit?.ai?.maturity || 'n/a'}
          </span>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{t('modules.improvement.dashboard.cockpit.subtitle')}</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          {(cockpit?.ai?.alerts || []).map((alert, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-800 dark:text-rose-200 text-sm">
              {alert}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <button type="button" onClick={() => runAiInsight('rootCause')} className="px-3 py-2 rounded-lg bg-rose-600 text-white text-sm hover:bg-rose-700 transition-all">{t('modules.improvement.dashboard.cockpit.actions.rootCause')}</button>
          <button type="button" onClick={() => runAiInsight('tracker')} className="px-3 py-2 rounded-lg bg-amber-600 text-white text-sm hover:bg-amber-700 transition-all">{t('modules.improvement.dashboard.cockpit.actions.tracker')}</button>
          <button type="button" onClick={() => runAiInsight('optimizer')} className="px-3 py-2 rounded-lg bg-emerald-600 text-white text-sm hover:bg-emerald-700 transition-all">{t('modules.improvement.dashboard.cockpit.actions.optimizer')}</button>
        </div>
        {(aiInsights.rootCause || aiInsights.tracker || aiInsights.optimizer) && (
          <div className="mt-4 p-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 text-sm text-slate-700 dark:text-slate-200 space-y-2">
            {aiInsights.rootCause?.suggestions && <p>{t('modules.improvement.dashboard.cockpit.summary.rootCause').replace('{count}', aiInsights.rootCause.suggestions.length)}</p>}
            {aiInsights.tracker?.summary && <p>{t('modules.improvement.dashboard.cockpit.summary.tracker').replace('{count}', aiInsights.tracker.summary.overdue || 0)}</p>}
            {aiInsights.optimizer?.next_wave && <p>{t('modules.improvement.dashboard.cockpit.summary.optimizer').replace('{count}', aiInsights.optimizer.next_wave.length)}</p>}
          </div>
        )}
      </div>

      {stats.nonconformities.critical > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-500/20 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">🚨</span>
            <h2 className="text-xl font-bold text-red-800 dark:text-red-100">{t('modules.improvement.dashboard.alerts.attentionRequired')}</h2>
          </div>
          <p className="text-red-700 dark:text-red-200">{t('modules.improvement.dashboard.alerts.criticalNcMessage').replace('{count}', stats.nonconformities.critical)}</p>
          <Link to="/improvement/nonconformities" className="inline-block mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all">
            {t('modules.improvement.dashboard.alerts.viewCriticalNc')}
          </Link>
        </div>
      )}

      {stats.corrective_actions.overdue > 0 && (
        <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-500/20 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">⏰</span>
            <h2 className="text-xl font-bold text-orange-800 dark:text-orange-100">{t('modules.improvement.dashboard.alerts.overdueActions')}</h2>
          </div>
          <p className="text-orange-700 dark:text-orange-200">{t('modules.improvement.dashboard.alerts.overdueMessage').replace('{count}', stats.corrective_actions.overdue)}</p>
          <Link to="/improvement/corrective-actions" className="inline-block mt-4 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-all">
            {t('modules.improvement.dashboard.alerts.viewOverdue')}
          </Link>
        </div>
      )}

      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6 shadow dark:shadow-slate-900/50">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">{t('modules.improvement.dashboard.quickActions.title')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link to="/improvement/nonconformities/new" className="flex items-center space-x-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-all">
            <span className="text-2xl">🚨</span>
            <div><p className="font-medium text-slate-900 dark:text-white">{t('modules.improvement.dashboard.quickActions.reportNc')}</p><p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.improvement.dashboard.quickActions.registerNc')}</p></div>
          </Link>
          <Link to="/improvement/corrective-actions/new" className="flex items-center space-x-3 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg hover:bg-orange-500/20 transition-all">
            <span className="text-2xl">🔧</span>
            <div><p className="font-medium text-slate-900 dark:text-white">{t('modules.improvement.dashboard.quickActions.newCorrectiveAction')}</p><p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.improvement.dashboard.quickActions.createActionPlan')}</p></div>
          </Link>
          <Link to="/improvement/continual/new" className="flex items-center space-x-3 p-4 bg-green-500/10 border border-green-500/20 rounded-lg hover:bg-green-500/20 transition-all">
            <span className="text-2xl">📈</span>
            <div><p className="font-medium text-slate-900 dark:text-white">{t('modules.improvement.dashboard.quickActions.improvementInitiative')}</p><p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.improvement.dashboard.quickActions.proposeContinual')}</p></div>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link to="/improvement/nonconformities" className="p-6 bg-gradient-to-br from-red-500/10 to-red-600/5 border border-red-500/20 rounded-lg hover:shadow-lg transition-all">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">📋</span>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">{t('modules.improvement.dashboard.cards.ncAndActionsTitle')}</h3>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">{t('modules.improvement.dashboard.cards.ncAndActionsDesc')}</p>
        </Link>
        <Link to="/improvement/continual" className="p-6 bg-gradient-to-br from-green-500/10 to-green-600/5 border border-green-500/20 rounded-lg hover:shadow-lg transition-all">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">🚀</span>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">{t('modules.improvement.dashboard.cards.continualTitle')}</h3>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">{t('modules.improvement.dashboard.cards.continualDesc')}</p>
        </Link>
      </div>
    </div>
  );
};

export default ImprovementDashboard;