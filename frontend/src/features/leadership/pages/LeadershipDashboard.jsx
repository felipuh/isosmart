// features/leadership/pages/LeadershipDashboard.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getPolicies, getRoles, getCommitments, getCockpitKPIs } from '../api/leadershipApi';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';

const LeadershipDashboard = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;
  const [cockpit, setCockpit] = useState(null);
  const [cockpitError, setCockpitError] = useState(false);
  const [stats, setStats] = useState({
    policies: { total: 0, active: 0, draft: 0 },
    roles: { total: 0, assigned: 0 },
    commitments: { total: 0, completed: 0, pending: 0 }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  const loadDashboardData = async () => {
    if (!orgId) {
      setStats({
        policies: { total: 0, active: 0, draft: 0 },
        roles: { total: 0, assigned: 0 },
        commitments: { total: 0, completed: 0, pending: 0 }
      });
      setLoading(false);
      return;
    }

    try {
      setLoading(true);

      const params = { organization_id: orgId };

      // Cockpit KPIs (enhanced)
      try {
        const kpis = await getCockpitKPIs();
        setCockpit(kpis);
      } catch { setCockpitError(true); }

      // Cargar políticas
      const policiesData = await getPolicies(params);
      const policies = Array.isArray(policiesData) ? policiesData : policiesData.results || [];

      // Cargar roles
      const rolesData = await getRoles(params);
      const roles = Array.isArray(rolesData) ? rolesData : rolesData.results || [];

      // Cargar compromisos
      const commitmentsData = await getCommitments(params);
      const commitments = Array.isArray(commitmentsData) ? commitmentsData : commitmentsData.results || [];
      
      setStats({
        policies: {
          total: policies.length,
          active: policies.filter(p => p.status === 'active').length,
          draft: policies.filter(p => p.status === 'draft').length
        },
        roles: {
          total: roles.length,
          assigned: roles.filter(r => r.is_active).length
        },
        commitments: {
          total: commitments.length,
          completed: commitments.filter(c => c.status === 'completed').length,
          pending: commitments.filter(c => c.status === 'planned' || c.status === 'in_progress').length
        }
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const colorMap = {
    blue: {
      gradient: 'from-blue-500/10 to-blue-600/5',
      border: 'border-blue-500/20',
      text: 'text-blue-600 dark:text-blue-400',
      shadow: 'hover:shadow-blue-500/20'
    },
    purple: {
      gradient: 'from-purple-500/10 to-purple-600/5',
      border: 'border-purple-500/20',
      text: 'text-purple-600 dark:text-purple-400',
      shadow: 'hover:shadow-purple-500/20'
    },
    green: {
      gradient: 'from-green-500/10 to-green-600/5',
      border: 'border-green-500/20',
      text: 'text-green-600 dark:text-green-400',
      shadow: 'hover:shadow-green-500/20'
    },
    orange: {
      gradient: 'from-orange-500/10 to-orange-600/5',
      border: 'border-orange-500/20',
      text: 'text-orange-600 dark:text-orange-400',
      shadow: 'hover:shadow-orange-500/20'
    }
  };

  const StatCard = ({ title, value, subtitle, icon, link, color = 'blue' }) => {
    const palette = colorMap[color] || colorMap.blue;

    return (
    <Link to={link} className="block">
      <div className={`bg-gradient-to-br ${palette.gradient} border ${palette.border} rounded-lg p-6 hover:shadow-lg ${palette.shadow} transition-all duration-300 bg-white dark:bg-slate-800 shadow dark:shadow-slate-900/50 border-slate-200 dark:border-slate-700`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-slate-600 dark:text-slate-300">{title}</h3>
          <span className="text-2xl">{icon}</span>
        </div>
        <div className="flex items-baseline">
          <p className={`text-3xl font-bold ${palette.text}`}>{value}</p>
        </div>
        {subtitle && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">{subtitle}</p>
        )}
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{t('modules.leadership.dashboard.title')}</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">{t('modules.leadership.dashboard.subtitle')}</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title={t('modules.leadership.dashboard.stats.policies.title')}
          value={stats.policies.total}
          subtitle={`${stats.policies.active} ${t('modules.leadership.dashboard.stats.policies.activeSuffix')}, ${stats.policies.draft} ${t('modules.leadership.dashboard.stats.policies.draftSuffix')}`}
          icon="📋"
          link="/leadership/policies"
          color="blue"
        />
        
        <StatCard
          title={t('modules.leadership.dashboard.stats.roles.title')}
          value={stats.roles.total}
          subtitle={`${stats.roles.assigned} ${t('modules.leadership.dashboard.stats.roles.assignedSuffix')}`}
          icon="👥"
          link="/leadership/roles"
          color="purple"
        />
        
        <StatCard
          title={t('modules.leadership.dashboard.stats.commitments.title')}
          value={stats.commitments.total}
          subtitle={`${stats.commitments.completed} ${t('modules.leadership.dashboard.stats.commitments.completedSuffix')}, ${stats.commitments.pending} ${t('modules.leadership.dashboard.stats.commitments.pendingSuffix')}`}
          icon="✅"
          link="/leadership/commitments"
          color="green"
        />
        
        <StatCard
          title={t('modules.leadership.dashboard.stats.raci.title')}
          value={t('modules.leadership.dashboard.stats.raci.value')}
          subtitle={t('modules.leadership.dashboard.stats.raci.subtitle')}
          icon="📊"
          link="/leadership/raci"
          color="orange"
        />
      </div>

      {/* Cockpit KPIs row */}
      {cockpit && !cockpitError && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title={t('modules.leadership.dashboard.cockpit.reviews')}
            value={cockpit.management_reviews?.total ?? '—'}
            subtitle={`${cockpit.management_reviews?.pending_count ?? 0} ${t('modules.leadership.dashboard.cockpit.pending')}`}
            icon="📋"
            link="/leadership/management-reviews"
            color="blue"
          />
          <StatCard
            title={t('modules.leadership.dashboard.cockpit.evidenceGraph')}
            value={cockpit.evidence_graph?.total_nodes ?? '—'}
            subtitle={`${cockpit.evidence_graph?.approved_nodes ?? 0} ${t('modules.leadership.dashboard.cockpit.approved')}`}
            icon="🕸"
            link="/leadership/evidence-graph"
            color="purple"
          />
          <StatCard
            title={t('modules.leadership.dashboard.cockpit.culture')}
            value={cockpit.culture_surveys?.active_count ?? '—'}
            subtitle={t('modules.leadership.dashboard.cockpit.activeSurveys')}
            icon="📝"
            link="/leadership/culture"
            color="green"
          />
          <StatCard
            title={t('modules.leadership.dashboard.cockpit.aiGovernance')}
            value={cockpit.ai_governance?.pending_decisions ?? '—'}
            subtitle={t('modules.leadership.dashboard.cockpit.pendingDecisions')}
            icon="🤖"
            link="/leadership/evidence-graph"
            color="orange"
          />
        </div>
      )}

      {/* Alerts from cockpit */}
      {cockpit?.alerts && cockpit.alerts.length > 0 && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-amber-800 dark:text-amber-200 mb-2">⚠️ {t('modules.leadership.dashboard.cockpit.alertsTitle')}</h3>
          <ul className="space-y-1">
            {cockpit.alerts.map((a, i) => (
              <li key={i} className="text-xs text-amber-700 dark:text-amber-300">• {a.message || a}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6 shadow dark:shadow-slate-900/50">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">{t('modules.leadership.dashboard.quickActions.title')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/leadership/policies/new"
            className="flex items-center space-x-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all"
          >
            <span className="text-2xl">📝</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.leadership.dashboard.quickActions.newPolicy')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.leadership.dashboard.quickActions.newPolicyDesc')}</p>
            </div>
          </Link>
          
          <Link
            to="/leadership/roles/new"
            className="flex items-center space-x-3 p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg hover:bg-purple-500/20 transition-all"
          >
            <span className="text-2xl">👤</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.leadership.dashboard.quickActions.newRole')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.leadership.dashboard.quickActions.newRoleDesc')}</p>
            </div>
          </Link>
          
          <Link
            to="/leadership/raci/new"
            className="flex items-center space-x-3 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg hover:bg-orange-500/20 transition-all"
          >
            <span className="text-2xl">📋</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.leadership.dashboard.quickActions.newRaci')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.leadership.dashboard.quickActions.newRaciDesc')}</p>
            </div>
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <Link
            to="/leadership/management-reviews"
            className="flex items-center space-x-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all"
          >
            <span className="text-2xl">📋</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.leadership.dashboard.quickActions.managementReviews')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.leadership.dashboard.quickActions.managementReviewsDesc')}</p>
            </div>
          </Link>
          <Link
            to="/leadership/evidence-graph"
            className="flex items-center space-x-3 p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg hover:bg-purple-500/20 transition-all"
          >
            <span className="text-2xl">🕸</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.leadership.dashboard.quickActions.evidenceGraph')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.leadership.dashboard.quickActions.evidenceGraphDesc')}</p>
            </div>
          </Link>
          <Link
            to="/leadership/auditor-pack"
            className="flex items-center space-x-3 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg hover:bg-amber-500/20 transition-all"
          >
            <span className="text-2xl">📦</span>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{t('modules.leadership.dashboard.quickActions.auditorPack')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.leadership.dashboard.quickActions.auditorPackDesc')}</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6 shadow dark:shadow-slate-900/50">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">{t('modules.leadership.dashboard.recentActivity.title')}</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-slate-100 dark:bg-slate-700/40 rounded-lg">
            <div className="flex items-center space-x-3">
              <span className="text-blue-400">📋</span>
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-white">{t('modules.leadership.dashboard.recentActivity.policyTitle')}</p>
                <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.leadership.dashboard.recentActivity.policyWhen')}</p>
              </div>
            </div>
            <span className="badge-base badge-warning">{t('modules.leadership.dashboard.recentActivity.draft')}</span>
          </div>
          
          <div className="flex items-center justify-between p-3 bg-slate-100 dark:bg-slate-700/40 rounded-lg">
            <div className="flex items-center space-x-3">
              <span className="text-purple-400">👥</span>
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-white">{t('modules.leadership.dashboard.recentActivity.qualityDirector')}</p>
                <p className="text-xs text-slate-600 dark:text-slate-400">{t('modules.leadership.dashboard.recentActivity.roleWhen')}</p>
              </div>
            </div>
            <span className="badge-base badge-success">{t('modules.leadership.dashboard.recentActivity.active')}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeadershipDashboard;