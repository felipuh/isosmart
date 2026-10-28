import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Network, 
  TrendingUp, 
  Target, 
  Workflow, 
  CheckCircle2, 
  ArrowRight,
  Award,
  Activity,
  FileText,
  BarChart3,
  CreditCard,
  CalendarClock
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import { useTheme } from '../../context/ThemeContext';
import api from '../../services/api';
import settingsService from '../../services/settingsService';

const Dashboard = () => {
  const { currentOrganization, user } = useAuth();
  const { t, language, translateBackendString } = useI18n();
  const { isDark } = useTheme();
  const orgId = currentOrganization?.id || null;
  const [stats, setStats] = useState({
    modulesActive: 0,
    totalModules: 7,
    clause4Progress: 0,
    iso9001Progress: 0,
    totalProcesses: 0,
    totalStakeholders: 0,
    lastUpdate: new Date().toISOString(),
  });
  const [clauseProgress, setClauseProgress] = useState([]);
  const [onboardingInsights, setOnboardingInsights] = useState(null);
  const [onboardingIsoSkeleton, setOnboardingIsoSkeleton] = useState(null);
  const [onboardingAdaptiveRoute, setOnboardingAdaptiveRoute] = useState(null);
  const [billingSummary, setBillingSummary] = useState(null);
  const statsRequestInFlightRef = useRef(false);
  const lastStatsLoadRef = useRef({ orgId: null, at: 0 });

  const normalizeCount = (data) => {
    if (Array.isArray(data)) return data.length;
    if (Array.isArray(data?.results)) return data.results.length;
    if (typeof data?.count === 'number') return data.count;
    return 0;
  };

  const fetchCount = useCallback(async (endpoint) => {
    try {
      const response = await api.get(endpoint, { params: { organization_id: orgId } });
      return normalizeCount(response.data);
    } catch {
      return 0;
    }
  }, [orgId]);

  const loadDashboardStats = useCallback(async () => {
    if (!orgId) return;

    const now = Date.now();
    const wasRecentlyLoaded =
      lastStatsLoadRef.current.orgId === orgId &&
      now - lastStatsLoadRef.current.at < 10000;

    if (statsRequestInFlightRef.current || wasRecentlyLoaded) {
      return;
    }

    statsRequestInFlightRef.current = true;

    const clauseChecks = [
      { id: '4', labelKey: 'dashboard.main.clauseProgress.clause4', checks: ['/context/history/', '/stakeholders/stakeholders/', '/scope/scopes/', '/processes/maps/'] },
      { id: '5', labelKey: 'dashboard.main.clauseProgress.clause5', checks: ['/leadership/policies/', '/leadership/commitments/', '/leadership/roles/'] },
      { id: '6', labelKey: 'dashboard.main.clauseProgress.clause6', checks: ['/planning/risks-opportunities/', '/planning/objectives/', '/planning/actions/'] },
      { id: '7', labelKey: 'dashboard.main.clauseProgress.clause7', checks: ['/resources/resources/', '/resources/competences/', '/resources/trainings/'] },
      { id: '8', labelKey: 'dashboard.main.clauseProgress.clause8', checks: ['/operations/requirements/', '/operations/providers/', '/operations/nonconformities/'] },
      { id: '9', labelKey: 'dashboard.main.clauseProgress.clause9', checks: ['/performance/measurements/', '/performance/findings/', '/performance/reviews/'] },
      { id: '10', labelKey: 'dashboard.main.clauseProgress.clause10', checks: ['/improvement/nonconformities/', '/improvement/corrective-actions/', '/improvement/continual-improvements/'] },
    ];

    try {
      const [processCount, stakeholderCount, clauseResults] = await Promise.all([
        fetchCount('/processes/maps/'),
        fetchCount('/stakeholders/stakeholders/'),
        Promise.all(
          clauseChecks.map(async (clause) => {
            const values = await Promise.all(clause.checks.map((endpoint) => fetchCount(endpoint)));
            const completed = values.filter((value) => value > 0).length;
            const progress = Math.round((completed / clause.checks.length) * 100);
            return { ...clause, progress };
          })
        ),
      ]);

      const iso9001Progress = clauseResults.length
        ? Math.round(clauseResults.reduce((acc, clause) => acc + clause.progress, 0) / clauseResults.length)
        : 0;

      setClauseProgress(clauseResults);
      setStats({
        modulesActive: clauseResults.filter((clause) => clause.progress > 0).length,
        totalModules: clauseResults.length,
        clause4Progress: clauseResults.find((clause) => clause.id === '4')?.progress || 0,
        iso9001Progress,
        totalProcesses: processCount,
        totalStakeholders: stakeholderCount,
        lastUpdate: new Date().toISOString(),
      });
    } finally {
      statsRequestInFlightRef.current = false;
      lastStatsLoadRef.current = { orgId, at: Date.now() };
    }
  }, [fetchCount, orgId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadDashboardStats();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadDashboardStats]);

  useEffect(() => {
    let mounted = true;

    const loadInsights = async () => {
      if (!orgId) return;
      try {
        const data = await settingsService.getOnboardingInsights(orgId, false, language);
        if (mounted) setOnboardingInsights(data);
      } catch {
        if (mounted) setOnboardingInsights(null);
      }
    };

    loadInsights();
    return () => {
      mounted = false;
    };
  }, [orgId, language]);

  useEffect(() => {
    let mounted = true;

    const loadBillingSummary = async () => {
      if (!orgId) return;
      try {
        const data = await settingsService.getBillingCurrent(orgId);
        if (!mounted) return;

        const subscription = data?.subscription || null;
        const recentPayments = data?.recent_payments || [];
        const pendingPayments = recentPayments.filter((payment) => payment.status === 'pending').length;

        setBillingSummary({
          subscription,
          pendingPayments,
        });
      } catch {
        if (mounted) setBillingSummary(null);
      }
    };

    loadBillingSummary();
    return () => {
      mounted = false;
    };
  }, [orgId]);

  const billingStatusBadge = {
    active: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    past_due: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    suspended: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    cancelled: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
  };

  const billingStatusLabel = {
    active: t('settings.billing.status.active'),
    past_due: t('settings.billing.status.pastDue'),
    suspended: t('settings.billing.status.suspended'),
    cancelled: t('settings.billing.status.cancelled'),
  };

  const getBillingHealth = (subscription) => {
    if (!subscription) return null;

    if (subscription.status === 'suspended' || subscription.status === 'cancelled') {
      return {
        label: t('dashboard.billing.health.critical'),
        detail: t('dashboard.billing.health.suspendedOrCancelled'),
        badgeClass: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
        dotClass: 'bg-red-500',
      };
    }

    if (!subscription.next_due_date) {
      return {
        label: t('dashboard.billing.health.stable'),
        detail: t('dashboard.billing.health.noDueDate'),
        badgeClass: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
        dotClass: 'bg-emerald-500',
      };
    }

    const dueDate = new Date(subscription.next_due_date);
    const today = new Date();
    dueDate.setHours(0, 0, 0, 0);
    today.setHours(0, 0, 0, 0);

    const msDiff = today.getTime() - dueDate.getTime();
    const overdueDays = Math.floor(msDiff / (1000 * 60 * 60 * 24));
    const graceDays = Number(subscription.grace_days || 0);

    if (overdueDays <= 0) {
      const remainingDays = Math.abs(overdueDays);
      const stableDetail = remainingDays === 0
        ? t('dashboard.billing.health.dueToday')
        : t('dashboard.billing.health.daysToDue', `${remainingDays} day(s) to due`).replace('{days}', remainingDays);
      return {
        label: t('dashboard.billing.health.stable'),
        detail: stableDetail,
        badgeClass: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
        dotClass: 'bg-emerald-500',
      };
    }

    if (overdueDays <= graceDays) {
      return {
        label: t('dashboard.billing.health.attention'),
        detail: t('dashboard.billing.health.daysOverdue', `With ${overdueDays} overdue day(s)`).replace('{days}', overdueDays),
        badgeClass: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
        dotClass: 'bg-amber-500',
      };
    }

    return {
      label: t('dashboard.billing.health.critical'),
      detail: t('dashboard.billing.health.overGrace', `Over grace period (${overdueDays} day(s))`).replace('{days}', overdueDays),
      badgeClass: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
      dotClass: 'bg-red-500',
    };
  };

  const translateScopeDraft = useCallback((scopeDraft) => {
    if (!scopeDraft || typeof scopeDraft !== 'string') return scopeDraft;

    // Option 3: if not in Spanish, always render the fixed i18n key regardless of backend text
    if (language !== 'es-LATAM') {
      return t('dashboard.main.isoSkeleton.scopeDraftFallback', scopeDraft);
    }

    return scopeDraft;
  }, [language, t]);

  useEffect(() => {
    let mounted = true;

    const loadAdaptiveRoute = async () => {
      if (!orgId) return;
      try {
        const data = await settingsService.getOnboardingAdaptiveRoute(orgId, language);
        if (mounted) setOnboardingAdaptiveRoute(data?.adaptive_route || null);
      } catch {
        if (mounted) setOnboardingAdaptiveRoute(null);
      }
    };

    loadAdaptiveRoute();
    return () => {
      mounted = false;
    };
  }, [orgId, language]);

  useEffect(() => {
    let mounted = true;

    const loadIsoSkeleton = async () => {
      if (!orgId) return;
      try {
        const data = await settingsService.getOnboardingIsoSkeleton(orgId, language);
        if (mounted) setOnboardingIsoSkeleton(data?.iso_skeleton || null);
      } catch {
        if (mounted) setOnboardingIsoSkeleton(null);
      }
    };

    loadIsoSkeleton();
    return () => {
      mounted = false;
    };
  }, [orgId, language]);

  const modules = [
    {
      id: 'sca',
      nameKey: 'dashboard.main.modulesCatalog.sca.name',
      code: 'SCA',
      isoKey: 'dashboard.main.modulesCatalog.sca.iso',
      descriptionKey: 'dashboard.main.modulesCatalog.sca.description',
      icon: TrendingUp,
      color: 'bg-blue-500',
      accentClass: 'text-blue-700 dark:text-blue-300',
      surfaceLight: '#eff6ff',
      surfaceDark: 'rgba(30, 58, 138, 0.30)',
      borderLight: '#bfdbfe',
      borderDark: 'rgba(30, 64, 175, 0.70)',
      route: '/context',
      status: 'active',
      featuresKey: [
        'dashboard.main.modulesCatalog.sca.features.swot',
        'dashboard.main.modulesCatalog.sca.features.risks',
        'dashboard.main.modulesCatalog.sca.features.trends',
      ]
    },
    {
      id: 'sie',
      nameKey: 'dashboard.main.modulesCatalog.sie.name',
      code: 'SIE',
      isoKey: 'dashboard.main.modulesCatalog.sie.iso',
      descriptionKey: 'dashboard.main.modulesCatalog.sie.description',
      icon: Network,
      color: 'bg-green-500',
      accentClass: 'text-green-700 dark:text-green-300',
      surfaceLight: '#ecfdf5',
      surfaceDark: 'rgba(6, 78, 59, 0.28)',
      borderLight: '#bbf7d0',
      borderDark: 'rgba(21, 128, 61, 0.65)',
      route: '/stakeholders',
      status: 'active',
      featuresKey: [
        'dashboard.main.modulesCatalog.sie.features.networkAnalysis',
        'dashboard.main.modulesCatalog.sie.features.powerInterestMatrix',
        'dashboard.main.modulesCatalog.sie.features.criticalStakeholders',
      ]
    },
    {
      id: 'asb',
      nameKey: 'dashboard.main.modulesCatalog.asb.name',
      code: 'ASB',
      isoKey: 'dashboard.main.modulesCatalog.asb.iso',
      descriptionKey: 'dashboard.main.modulesCatalog.asb.description',
      icon: Target,
      color: 'bg-purple-500',
      accentClass: 'text-purple-700 dark:text-purple-300',
      surfaceLight: '#faf5ff',
      surfaceDark: 'rgba(88, 28, 135, 0.27)',
      borderLight: '#e9d5ff',
      borderDark: 'rgba(126, 34, 206, 0.60)',
      route: '/scope',
      status: 'active',
      featuresKey: [
        'dashboard.main.modulesCatalog.asb.features.qmsScope',
        'dashboard.main.modulesCatalog.asb.features.applicableRequirements',
        'dashboard.main.modulesCatalog.asb.features.justifiedExclusions',
      ]
    },
    {
      id: 'spm',
      nameKey: 'dashboard.main.modulesCatalog.spm.name',
      code: 'SPM',
      isoKey: 'dashboard.main.modulesCatalog.spm.iso',
      descriptionKey: 'dashboard.main.modulesCatalog.spm.description',
      icon: Workflow,
      color: 'bg-orange-500',
      accentClass: 'text-orange-700 dark:text-orange-300',
      surfaceLight: '#fff7ed',
      surfaceDark: 'rgba(124, 45, 18, 0.28)',
      borderLight: '#fed7aa',
      borderDark: 'rgba(194, 65, 12, 0.60)',
      route: '/processes',
      status: 'active',
      featuresKey: [
        'dashboard.main.modulesCatalog.spm.features.processMap',
        'dashboard.main.modulesCatalog.spm.features.interactions',
        'dashboard.main.modulesCatalog.spm.features.criticalityAnalysis',
      ]
    }
  ];

  const quickActions = [
    {
      title: t('dashboard.quickActions.analyzeContext'),
      description: t('dashboard.quickActions.analyzeContextDesc'),
      icon: TrendingUp,
      route: '/context',
      color: 'bg-blue-500'
    },
    {
      title: t('dashboard.quickActions.manageStakeholders'),
      description: t('dashboard.quickActions.manageStakeholdersDesc'),
      icon: Network,
      route: '/stakeholders',
      color: 'bg-green-500'
    },
    {
      title: t('dashboard.quickActions.defineScope'),
      description: t('dashboard.quickActions.defineScopeDesc'),
      icon: Target,
      route: '/scope',
      color: 'bg-purple-500'
    },
    {
      title: t('dashboard.quickActions.mapProcesses'),
      description: t('dashboard.quickActions.mapProcessesDesc'),
      icon: Workflow,
      route: '/processes',
      color: 'bg-orange-500'
    }
  ];

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen transition-colors duration-300">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            {t('dashboard.main.systemTitle')}
          </h1>
          {user && (
            <div className="text-right">
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                {user.first_name} {user.last_name}
              </p>
              <p className="text-xs text-slate-500">
                {t('dashboard.lastAccessLabel')}: {new Date().toLocaleDateString(language === 'es-LATAM' ? 'es-ES' : language)}
              </p>
            </div>
          )}
        </div>
        <p className="text-slate-600 dark:text-slate-400">
          {currentOrganization?.name || t('dashboard.noOrganization')} | {t('dashboard.main.standardsLine')}
        </p>
      </div>

      <div className="mb-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center mb-2">
              <Award className="h-8 w-8 mr-3" />
              <h2 className="text-2xl font-bold">{t('dashboard.main.globalComplianceTitle')}</h2>
            </div>
            <p className="text-blue-100">
              {t('dashboard.main.progressByClause')}
            </p>
          </div>
          <div className="text-right">
            <div className="text-6xl font-bold">{stats.iso9001Progress}%</div>
            <div className="text-sm text-blue-100">{t('dashboard.main.averageClauses')}</div>
          </div>
        </div>
      </div>

      {onboardingInsights && (
        <div className="mb-8 bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{t('dashboard.main.onboardingInsights.title')}</h2>
            <span className="text-xs px-2 py-1 rounded bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">
              v{onboardingInsights.version}
            </span>
          </div>

          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
            {translateBackendString(onboardingInsights.summary_output?.message) || t('dashboard.main.onboardingInsights.defaultMessage')}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2">{t('dashboard.main.onboardingInsights.quickWins')}</p>
              <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1">
                {(onboardingInsights.impact_savings_output?.quick_wins || []).slice(0, 3).map((item, index) => (
                  <li key={`qw-${index}`}>• {translateBackendString(item)}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2">{t('dashboard.main.onboardingInsights.bigBets')}</p>
              <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1">
                {(onboardingInsights.impact_savings_output?.big_bets || []).slice(0, 3).map((item, index) => (
                  <li key={`bb-${index}`}>• {translateBackendString(item)}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2">{t('dashboard.main.onboardingInsights.nextFocus')}</p>
              <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1">
                {(onboardingInsights.summary_output?.top_priorities_today || []).slice(0, 3).map((item, index) => (
                  <li key={`tp-${index}`}>• {translateBackendString(item)}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {onboardingIsoSkeleton && (
        <div className="mb-8 bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{t('dashboard.main.isoSkeleton.title')}</h2>
            <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
              {t('dashboard.main.isoSkeleton.systemReady').replace('{percentage}', onboardingIsoSkeleton.system_readiness?.score_percentage || 0)}
            </span>
          </div>

          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
            {translateScopeDraft(onboardingIsoSkeleton.scope_draft)}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2">{t('dashboard.main.isoSkeleton.initialProcesses')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                {t('dashboard.main.isoSkeleton.processCounts')
                  .replace('{strategic}', (onboardingIsoSkeleton.initial_process_map?.strategic || []).length)
                  .replace('{operational}', (onboardingIsoSkeleton.initial_process_map?.operational || []).length)
                  .replace('{support}', (onboardingIsoSkeleton.initial_process_map?.support || []).length)}
              </p>
            </div>

            <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2">{t('dashboard.main.isoSkeleton.risksOpportunities')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                {t('dashboard.main.isoSkeleton.risksOpportunitiesCounts')
                  .replace('{risks}', (onboardingIsoSkeleton.top_5_risks || []).length)
                  .replace('{opportunities}', (onboardingIsoSkeleton.top_5_opportunities || []).length)}
              </p>
            </div>

            <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2">{t('dashboard.main.isoSkeleton.objectivesV1')}</p>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                {t('dashboard.main.isoSkeleton.objectivesGenerated')
                  .replace('{count}', (onboardingIsoSkeleton.quality_objectives_v1 || []).length)}
              </p>
            </div>
          </div>
        </div>
      )}

      {onboardingAdaptiveRoute && (
        <div className="mb-8 bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{t('dashboard.main.adaptiveRoute.title')}</h2>
            <span className="text-xs px-2 py-1 rounded bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300">
              {translateBackendString(onboardingAdaptiveRoute.mode)} · {translateBackendString(onboardingAdaptiveRoute.cadence)}
            </span>
          </div>

          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-1">{translateBackendString(onboardingAdaptiveRoute.title)}</p>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{translateBackendString(onboardingAdaptiveRoute.description)}</p>

          <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2">{t('dashboard.main.adaptiveRoute.suggestedActions')}</p>
            <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1">
              {(onboardingAdaptiveRoute.recommended_actions || []).slice(0, 4).map((item, index) => (
                <li key={`ra-${index}`}>• {translateBackendString(item)}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {billingSummary?.subscription && (
        <div className="mb-8 bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          {(() => {
            const billingHealth = getBillingHealth(billingSummary.subscription);
            return (
              <>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-1">{t('dashboard.billing.title')}</h2>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('dashboard.billing.subtitle')}</p>
            </div>
            <CreditCard className="h-6 w-6 text-indigo-500" />
          </div>

          {billingHealth && (
            <div className="mt-4 flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${billingHealth.dotClass}`} />
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{t('dashboard.billing.trafficLight')}: {billingHealth.label}</p>
              </div>
              <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${billingHealth.badgeClass}`}>
                {billingHealth.detail}
              </span>
            </div>
          )}

          <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">{t('dashboard.billing.currentStatus')}</p>
              <span className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${billingStatusBadge[billingSummary.subscription.status] || billingStatusBadge.cancelled}`}>
                {billingStatusLabel[billingSummary.subscription.status] || billingSummary.subscription.status}
              </span>
            </div>

            <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">{t('dashboard.billing.nextCharge')}</p>
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <CalendarClock className="h-4 w-4 text-indigo-500" />
                {billingSummary.subscription.next_due_date
                  ? new Date(billingSummary.subscription.next_due_date).toLocaleDateString(language === 'es-LATAM' ? 'es-ES' : language)
                  : t('dashboard.billing.noDate')}
              </p>
            </div>

            <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">{t('dashboard.billing.monthlyAndPending')}</p>
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                {billingSummary.subscription.monthly_price} {billingSummary.subscription.currency}
              </p>
              <p className="text-xs mt-2 text-slate-500 dark:text-slate-400">
                {t('dashboard.billing.pendingPayments', '{count} payment(s) pending').replace('{count}', billingSummary.pendingPayments)}
              </p>
            </div>
          </div>

          <div className="mt-4">
            <Link to="/settings" className="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:underline">
              {t('dashboard.billing.goToSettings')} →
            </Link>
          </div>
              </>
            );
          })()}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">{t('dashboard.main.cards.clausesWithProgress')}</p>
              <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                {stats.modulesActive}/{stats.totalModules}
              </p>
            </div>
            <CheckCircle2 className="h-12 w-12 text-green-400" />
          </div>
          <div className="mt-4">
            <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
              <div
                className="bg-green-500 dark:bg-green-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${stats.totalModules ? Math.round((stats.modulesActive / stats.totalModules) * 100) : 0}%` }}
              />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">{t('dashboard.main.cards.isoClause4')}</p>
              <p className="text-3xl font-bold text-blue-600">{stats.clause4Progress}%</p>
            </div>
            <Target className="h-12 w-12 text-blue-400" />
          </div>
          <div className="mt-4">
            <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
              <div 
                className="bg-blue-500 dark:bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${stats.clause4Progress}%` }}
              />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">{t('dashboard.main.cards.mappedProcesses')}</p>
              <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">{stats.totalProcesses}</p>
            </div>
            <Workflow className="h-12 w-12 text-purple-400" />
          </div>
          <div className="mt-2">
            <p className="text-xs text-slate-500 dark:text-slate-400">{t('dashboard.main.cards.mappedProcessesDetail')}</p>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">{t('dashboard.main.cards.stakeholders')}</p>
              <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">{stats.totalStakeholders}</p>
            </div>
            <Activity className="h-12 w-12 text-orange-400" />
          </div>
          <div className="mt-2">
            <p className="text-xs text-slate-500 dark:text-slate-400">{t('dashboard.main.cards.stakeholdersDetail')}</p>
          </div>
        </div>
      </div>

      {/* Módulos Grid */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">{t('dashboard.main.modulesTitle')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {modules.map((module) => {
            const Icon = module.icon;
            const moduleName = module.nameKey ? t(module.nameKey) : module.name;
            const moduleDescription = module.descriptionKey ? t(module.descriptionKey) : module.description;
            const moduleIso = module.isoKey ? t(module.isoKey) : module.iso;
            const moduleFeatures = Array.isArray(module.features)
              ? module.features
              : Array.isArray(module.featuresKey)
                ? module.featuresKey.map((key) => t(key))
                : [];
            return (
              <Link
                key={module.id}
                to={module.route}
                className="border-2 rounded-lg p-6 shadow-sm dark:shadow-slate-950/30 hover:shadow-lg dark:hover:shadow-slate-950/60 transition-all duration-200 hover:scale-[1.02]"
                style={{
                  backgroundColor: isDark ? module.surfaceDark : module.surfaceLight,
                  borderColor: isDark ? module.borderDark : module.borderLight,
                }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className={`${module.color} p-3 rounded-lg mr-4`}>
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white">{moduleName}</h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400">{module.code} • {moduleIso}</p>
                    </div>
                  </div>
                  <span className="flex items-center text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-2 py-1 rounded-full font-semibold">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    {t('common.labels.active').toUpperCase()}
                  </span>
                </div>
                
                <p className="text-sm text-slate-700 dark:text-slate-300 mb-4">{moduleDescription}</p>
                
                <div className="space-y-2">
                  {moduleFeatures.map((feature, idx) => (
                    <div key={idx} className="flex items-center text-sm text-slate-600 dark:text-slate-400">
                      <CheckCircle2 className="h-4 w-4 text-green-500 dark:text-green-400 mr-2" />
                      {feature}
                    </div>
                  ))}
                </div>

                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between">
                  <span className={`text-sm font-semibold ${module.accentClass}`}>
                    {t('dashboard.main.viewDashboard')}
                  </span>
                  <ArrowRight className={`h-5 w-5 ${module.accentClass}`} />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">{t('dashboard.quickActions.title')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 dark:text-white gap-4">
          {quickActions.map((action, idx) => {
            const Icon = action.icon;
            return (
              <Link
                key={idx}
                to={action.route}
                className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-4 hover:shadow-lg transition-shadow"
              >
                <div className={`${action.color} w-10 h-10 rounded-lg flex items-center justify-center mb-3`}>
                  <Icon className="h-5 w-5 text-white" />
                </div>
                <h3 className="font-semibold text-slate-900 dark:text-white mb-1">{action.title}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">{action.description}</p>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Progress Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2 text-blue-500" />
            {t('dashboard.main.clauseProgress.title')}
          </h3>
          <div className="space-y-4">
            {clauseProgress.map((clause) => (
              <div key={clause.id}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t(clause.labelKey)}</span>
                  <span className="text-sm font-bold text-blue-600 dark:text-blue-400">{clause.progress}%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
                  <div className="bg-blue-500 dark:bg-blue-600 h-3 rounded-full" style={{ width: `${clause.progress}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center">
            <FileText className="h-5 w-5 mr-2 text-purple-500" />
            {t('dashboard.main.summary.title')}
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700">
              <span className="text-sm text-slate-600 dark:text-slate-400">{t('dashboard.main.summary.activeAiModules')}</span>
              <span className="text-sm font-bold text-slate-900 dark:text-slate-200">{stats.modulesActive}/{stats.totalModules}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700">
              <span className="text-sm text-slate-600 dark:text-slate-400">{t('dashboard.main.summary.isoRequirementsCovered')}</span>
              <span className="text-sm font-bold text-slate-900 dark:text-slate-200">{t('dashboard.main.summary.isoCoveredRange')}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700">
              <span className="text-sm text-slate-600 dark:text-slate-400">{t('dashboard.main.cards.mappedProcesses')}</span>
              <span className="text-sm font-bold text-slate-900 dark:text-slate-200">{stats.totalProcesses} {t('dashboard.main.summary.processesSuffix')}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700">
              <span className="text-sm text-slate-600 dark:text-slate-400">{t('dashboard.main.summary.isoCompliance')}</span>
              <span className="text-sm font-bold text-slate-900 dark:text-slate-200">{stats.iso9001Progress}%</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-slate-600 dark:text-slate-400">{t('dashboard.main.summary.systemStatus')}</span>
              <span className="text-sm font-bold text-green-600">{t('dashboard.main.summary.operational')}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white mb-1">{t('dashboard.main.footer.version')}</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              {t('dashboard.main.footer.subtitle')}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-slate-600 dark:text-slate-400">{t('dashboard.executive.lastUpdate')}</p>
            <p className="text-sm font-medium text-slate-900 dark:text-slate-300">
              {new Date(stats.lastUpdate).toLocaleDateString(language === 'es-LATAM' ? 'es-ES' : language, {
                day: '2-digit',
                month: 'long',
                year: 'numeric'
              })}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;