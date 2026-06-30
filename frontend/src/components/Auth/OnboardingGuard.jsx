import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import settingsService from '../../services/settingsService';

const getOnboardingSessionKey = (organizationId) => (
  organizationId ? `isosmart_onboarding_seen_${organizationId}` : null
);

const OnboardingGuard = ({ children }) => {
  const { currentOrganization, isAuthenticated } = useAuth();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(true);
  const [shownInSession, setShownInSession] = useState(false);

  const organizationId = currentOrganization?.id;
  const isOnboardingRoute = location.pathname === '/onboarding';

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

  useEffect(() => {
    const sessionKey = getOnboardingSessionKey(organizationId);
    if (!sessionKey || typeof window === 'undefined') {
      setShownInSession(false);
      return;
    }

    setShownInSession(window.sessionStorage.getItem(sessionKey) === '1');
  }, [organizationId, isAuthenticated]);

  useEffect(() => {
    const sessionKey = getOnboardingSessionKey(organizationId);
    if (!sessionKey || typeof window === 'undefined') {
      return;
    }

    if (completed) {
      window.sessionStorage.removeItem(sessionKey);
      if (shownInSession) {
        setShownInSession(false);
      }
      return;
    }

    if (isOnboardingRoute && !shownInSession) {
      window.sessionStorage.setItem(sessionKey, '1');
      setShownInSession(true);
    }
  }, [completed, isOnboardingRoute, organizationId, shownInSession]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (!completed && !isOnboardingRoute && !shownInSession) {
    return <Navigate to="/onboarding" replace />;
  }

  return children;
};

export default OnboardingGuard;
