import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AlertTriangle, Loader2, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import settingsService from '../../services/settingsService';

const ONBOARDING_STATUS_TIMEOUT_MS = 10000;

const OnboardingGuard = ({ children }) => {
  const { t } = useI18n();
  const { currentOrganization, isAuthenticated } = useAuth();
  const location = useLocation();
  const [status, setStatus] = useState('loading');
  const [validatedOrganizationId, setValidatedOrganizationId] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  const isOnboardingRoute = location.pathname === '/onboarding';

  useEffect(() => {
    let mounted = true;
    let timeoutId;

    const checkStatus = async () => {
      if (!isAuthenticated || !currentOrganization?.id) {
        if (mounted) {
          setValidatedOrganizationId(null);
          setStatus('degraded');
        }
        return;
      }

      try {
        setValidatedOrganizationId(null);
        setStatus('loading');
        const timeout = new Promise((_, reject) => {
          timeoutId = window.setTimeout(
            () => reject(new Error('onboarding_status_timeout')),
            ONBOARDING_STATUS_TIMEOUT_MS
          );
        });
        const data = await Promise.race([
          settingsService.getOnboardingStatus(currentOrganization.id),
          timeout,
        ]);
        if (typeof data?.onboarding_completed !== 'boolean') {
          throw new Error('invalid_onboarding_status');
        }
        if (mounted) {
          setValidatedOrganizationId(currentOrganization.id);
          setStatus(data.onboarding_completed ? 'completed' : 'incomplete');
        }
      } catch {
        if (mounted) {
          setValidatedOrganizationId(null);
          setStatus('degraded');
        }
      } finally {
        window.clearTimeout(timeoutId);
      }
    };

    checkStatus();
    return () => {
      mounted = false;
      window.clearTimeout(timeoutId);
    };
  }, [currentOrganization?.id, isAuthenticated, retryCount]);

  if (status === 'degraded') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 p-6">
        <div className="max-w-md rounded-xl border border-amber-300 bg-white dark:bg-slate-800 p-6 text-center shadow-sm" role="alert">
          <AlertTriangle className="w-10 h-10 text-amber-500 mx-auto mb-3" />
          <h1 className="text-lg font-semibold text-slate-900 dark:text-white">{t('onboardingGuard.degradedTitle')}</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{t('onboardingGuard.degradedDescription')}</p>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{t('onboardingGuard.support')}</p>
          <button
            type="button"
            onClick={() => setRetryCount((value) => value + 1)}
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            <RefreshCw className="w-4 h-4" />
            {t('common.buttons.retry')}
          </button>
        </div>
      </div>
    );
  }

  if (status === 'loading' || validatedOrganizationId !== currentOrganization?.id) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center" role="status" aria-live="polite">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mx-auto mb-3" />
          <p className="text-sm text-slate-600 dark:text-slate-300">{t('onboardingGuard.loading')}</p>
        </div>
      </div>
    );
  }

  if (status === 'incomplete' && !isOnboardingRoute) {
    return <Navigate to="/onboarding" replace />;
  }

  return children;
};

export default OnboardingGuard;
