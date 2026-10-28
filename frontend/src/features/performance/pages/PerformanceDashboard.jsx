// features/performance/pages/PerformanceDashboard.jsx
import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getIndicators,
  getMeasurements,
  getMeasurementStats,
  getAudits,
  getFindings,
  getReviews,
  getPerformanceCockpitKpis,
  analyzeIndicatorDriftAI,
  analyzeAuditAssistantAI,
  generateExecutiveBriefAI,
} from '../api/performanceApi';

const normalizeList = (data) => Array.isArray(data) ? data : data?.results || [];

const StatCard = ({ title, value, subtitle, icon, link, color = 'blue', statColors }) => {
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

const PerformanceDashboard = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const statColors = {
    blue: {
      card: 'from-blue-500/10 to-blue-600/5 border-blue-500/20 hover:shadow-blue-500/20',
      value: 'text-blue-600 dark:text-blue-400'
    },
    green: {
      card: 'from-green-500/10 to-green-600/5 border-green-500/20 hover:shadow-green-500/20',
      value: 'text-green-600 dark:text-green-400'
    },
    orange: {
      card: 'from-orange-500/10 to-orange-600/5 border-orange-500/20 hover:shadow-orange-500/20',
      value: 'text-orange-600 dark:text-orange-400'
    },
    red: {
      card: 'from-red-500/10 to-red-600/5 border-red-500/20 hover:shadow-red-500/20',
      value: 'text-red-600 dark:text-red-400'
    }
  };

  const [stats, setStats] = useState({
    indicators: { total: 0, active: 0 },
    measurements: { total: 0, on_target: 0, needs_attention: 0 },
    audits: { total: 0, planned: 0 },
    findings: { total: 0, open: 0 },
    reviews: { total: 0, scheduled: 0 }
  });
  const [loading, setLoading] = useState(true);
  const [cockpit, setCockpit] = useState(null);
  const [aiInsights, setAiInsights] = useState({
    drift: null,
    audit: null,
    executive: null,
  });

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [
        indicatorsData,
        measurementsData,
        auditsData,
        findingsData,
        reviewsData,
        measurementStats,
        cockpitData
      ] = await Promise.all([
        getIndicators({ organization_id: orgId }),
        getMeasurements({ organization_id: orgId }),
        getAudits({ organization_id: orgId }),
        getFindings({ organization_id: orgId }),
        getReviews({ organization_id: orgId }),
        getMeasurementStats(orgId),
        getPerformanceCockpitKpis(orgId).catch(() => null)
      ]);

      const indicators = normalizeList(indicatorsData);
      const measurements = normalizeList(measurementsData);
      const audits = normalizeList(auditsData);
      const findings = normalizeList(findingsData);
      const reviews = normalizeList(reviewsData);

      setStats({
        indicators: {
          total: indicators.length,
          active: indicators.filter(i => i.status === 'active').length
        },
        measurements: {
          total: measurements.length,
          on_target: measurementStats?.on_target ?? measurements.filter(m => m.status === 'on_target').length,
          needs_attention: measurementStats?.needs_attention ?? measurements.filter(m => m.status === 'needs_attention').length
        },
        audits: {
          total: audits.length,
          planned: audits.filter(a => a.status === 'planned').length
        },
        findings: {
          total: findings.length,
          open: findings.filter(f => f.status === 'open').length
        },
        reviews: {
          total: reviews.length,
          scheduled: reviews.filter(r => r.status === 'scheduled').length
        }
      });
      setCockpit(cockpitData);
    } catch (error) {
      console.error('Error loading performance dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    if (orgId) {
      loadDashboardData();
    }
  }, [orgId, loadDashboardData]);

  const runAiInsight = async (kind) => {
    if (!orgId) return;
    try {
      const actionMap = {
        drift: analyzeIndicatorDriftAI,
        audit: analyzeAuditAssistantAI,
        executive: generateExecutiveBriefAI,
      };
      const executor = actionMap[kind];
      if (!executor) return;
      const result = await executor(orgId);
      setAiInsights(prev => ({ ...prev, [kind]: result }));
    } catch (error) {
      console.error('Error generating performance AI insight:', error);
    }
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
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{t('modules.performance.dashboard.title')}</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">{t('modules.performance.dashboard.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title={t('modules.performance.dashboard.stats.indicators')}
          value={stats.indicators.total}
          subtitle={t('modules.performance.dashboard.stats.indicatorsActive').replace('{count}', stats.indicators.active)}
          icon="🎯"
          link="/performance/indicators"
          color="blue"
          statColors={statColors}
        />

        <StatCard
          title={t('modules.performance.dashboard.stats.measurements')}
          value={stats.measurements.total}
          subtitle={t('modules.performance.dashboard.stats.measurementsDetail')
            .replace('{onTarget}', stats.measurements.on_target)
            .replace('{needsAttention}', stats.measurements.needs_attention)}
          icon="📈"
          link="/performance/measurements"
          color="green"
          statColors={statColors}
        />

        <StatCard
          title={t('modules.performance.dashboard.stats.audits')}
          value={stats.audits.total}
          subtitle={t('modules.performance.dashboard.stats.auditsPlanned').replace('{count}', stats.audits.planned)}
          icon="🧾"
          link="/performance/audits"
          color="orange"
          statColors={statColors}
        />

        <StatCard
          title={t('modules.performance.dashboard.stats.findings')}
          value={stats.findings.total}
          subtitle={t('modules.performance.dashboard.stats.findingsOpen').replace('{count}', stats.findings.open)}
          icon="🔎"
          link="/performance/findings"
          color="red"
          statColors={statColors}
        />
      </div>

      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6 shadow dark:shadow-slate-900/50">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">{t('modules.performance.dashboard.cockpit.title')}</h2>
          <span className="text-xs px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200">
            {cockpit?.ai?.priority || 'n/a'}
          </span>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{t('modules.performance.dashboard.cockpit.subtitle')}</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          {(cockpit?.ai?.alerts || []).map((alert, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-800 dark:text-blue-200 text-sm">
              {alert}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <button type="button" onClick={() => runAiInsight('drift')} className="px-3 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-700 transition-all">{t('modules.performance.dashboard.cockpit.actions.drift')}</button>
          <button type="button" onClick={() => runAiInsight('audit')} className="px-3 py-2 rounded-lg bg-orange-600 text-white text-sm hover:bg-orange-700 transition-all">{t('modules.performance.dashboard.cockpit.actions.audit')}</button>
          <button type="button" onClick={() => runAiInsight('executive')} className="px-3 py-2 rounded-lg bg-teal-600 text-white text-sm hover:bg-teal-700 transition-all">{t('modules.performance.dashboard.cockpit.actions.executive')}</button>
        </div>
        {(aiInsights.drift || aiInsights.audit || aiInsights.executive) && (
          <div className="mt-4 p-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 text-sm text-slate-700 dark:text-slate-200 space-y-2">
            {aiInsights.drift?.drift_percentage !== undefined && <p>{t('modules.performance.dashboard.cockpit.summary.drift').replace('{value}', aiInsights.drift.drift_percentage)}</p>}
            {aiInsights.audit?.top_priority && <p>{t('modules.performance.dashboard.cockpit.summary.audit').replace('{count}', aiInsights.audit.top_priority.length)}</p>}
            {aiInsights.executive?.summary && <p>{t('modules.performance.dashboard.cockpit.summary.executive').replace('{count}', aiInsights.executive.summary.open_reviews || 0)}</p>}
          </div>
        )}
      </div>

      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6 shadow dark:shadow-slate-900/50">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">{t('modules.performance.dashboard.quickActions.title')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/performance/indicators"
            className="flex items-center space-x-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all"
          >
            <span className="text-2xl">🎯</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.performance.dashboard.quickActions.newIndicator')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.performance.dashboard.quickActions.defineKpi')}</p>
            </div>
          </Link>

          <Link
            to="/performance/measurements"
            className="flex items-center space-x-3 p-4 bg-green-500/10 border border-green-500/20 rounded-lg hover:bg-green-500/20 transition-all"
          >
            <span className="text-2xl">📈</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.performance.dashboard.quickActions.registerMeasurement')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.performance.dashboard.quickActions.captureResults')}</p>
            </div>
          </Link>

          <Link
            to="/performance/audits"
            className="flex items-center space-x-3 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg hover:bg-orange-500/20 transition-all"
          >
            <span className="text-2xl">🧾</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.performance.dashboard.quickActions.planAudit')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.performance.dashboard.quickActions.scheduleTracking')}</p>
            </div>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Link
          to="/performance/analyses"
          className="p-6 bg-gradient-to-br from-indigo-500/10 to-indigo-600/5 border border-indigo-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">🧠</span>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">{t('modules.performance.dashboard.cards.analysisTitle')}</h3>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">{t('modules.performance.dashboard.cards.analysisDesc')}</p>
        </Link>

        <Link
          to="/performance/reviews"
          className="p-6 bg-gradient-to-br from-teal-500/10 to-teal-600/5 border border-teal-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">📋</span>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">{t('modules.performance.dashboard.cards.managementReviewTitle')}</h3>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">{t('modules.performance.dashboard.cards.managementReviewDesc')}</p>
        </Link>

        <Link
          to="/performance/findings"
          className="p-6 bg-gradient-to-br from-rose-500/10 to-rose-600/5 border border-rose-500/20 rounded-lg hover:shadow-lg transition-all"
        >
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">🔎</span>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">{t('modules.performance.dashboard.cards.findingsTitle')}</h3>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">{t('modules.performance.dashboard.cards.findingsDesc')}</p>
        </Link>
      </div>
    </div>
  );
};

export default PerformanceDashboard;