/* eslint-disable react-refresh/only-export-components */

import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { useAuth } from './AuthContext';
import settingsService from '../services/settingsService';

const OnboardingStatusContext = createContext(null);
const ONBOARDING_STATUS_TIMEOUT_MS = 10000;

const initialState = {
  status: 'loading',
  organizationId: null,
};

export const useOnboardingStatus = () => {
  const context = useContext(OnboardingStatusContext);
  if (!context) {
    throw new Error('useOnboardingStatus must be used within OnboardingStatusProvider');
  }
  return context;
};

export const OnboardingStatusProvider = ({ children }) => {
  const { currentOrganization, isAuthenticated } = useAuth();
  const [state, setState] = useState(initialState);
  const requestIdRef = useRef(0);

  const refreshOnboardingStatus = useCallback(async () => {
    const organizationId = currentOrganization?.id;
    const requestId = ++requestIdRef.current;

    if (!isAuthenticated || !organizationId) {
      setState({ status: 'degraded', organizationId: null });
      return false;
    }

    setState({ status: 'loading', organizationId: null });
    let timeoutId;
    try {
      const timeout = new Promise((_, reject) => {
        timeoutId = window.setTimeout(
          () => reject(new Error('onboarding_status_timeout')),
          ONBOARDING_STATUS_TIMEOUT_MS,
        );
      });
      const data = await Promise.race([
        settingsService.getOnboardingStatus(organizationId),
        timeout,
      ]);
      if (typeof data?.onboarding_completed !== 'boolean') {
        throw new Error('invalid_onboarding_status');
      }
      if (requestId === requestIdRef.current) {
        setState({
          status: data.onboarding_completed ? 'completed' : 'incomplete',
          organizationId,
        });
      }
      return data.onboarding_completed;
    } catch {
      if (requestId === requestIdRef.current) {
        setState({ status: 'degraded', organizationId: null });
      }
      return false;
    } finally {
      window.clearTimeout(timeoutId);
    }
  }, [currentOrganization?.id, isAuthenticated]);

  useEffect(() => {
    void refreshOnboardingStatus();
  }, [refreshOnboardingStatus]);

  return (
    <OnboardingStatusContext.Provider value={{ ...state, refreshOnboardingStatus }}>
      {children}
    </OnboardingStatusContext.Provider>
  );
};

export default OnboardingStatusContext;
