import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import settingsService from '../../services/settingsService';

const OnboardingGuard = ({ children }) => {
  const { t } = useI18n();
  const { currentOrganization, isAuthenticated } = useAuth();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(true);

  useEffect(() => {
    let mounted = true;

    const checkStatus = async () => {
      if (!isAuthenticated || !currentOrganization?.id) {
        if (mounted) {
          setCompleted(true);
          setLoading(false);
        }
        return;
      }

      try {
        setLoading(true);
        const data = await settingsService.getOnboardingStatus(currentOrganization.id);
        if (mounted) {
          setCompleted(Boolean(data.onboarding_completed));
        }
      } catch {
        if (mounted) {
          setCompleted(true);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    checkStatus();
    return () => {
      mounted = false;
    };
  }, [currentOrganization?.id, isAuthenticated]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
      </div>
    );
  }

  const isOnboardingRoute = location.pathname === '/onboarding';

  if (!completed && !isOnboardingRoute) {
    return <Navigate to="/onboarding" replace />;
  }

  if (completed && isOnboardingRoute) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default OnboardingGuard;
