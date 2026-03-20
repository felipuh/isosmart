import React, { useEffect, useRef, useState } from 'react';
import { Activity, Bell, Moon, Settings, Sun } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import { useTheme } from '../../context/ThemeContext';
import { useFontSize } from '../../context/FontSizeContext';
import settingsService from '../../services/settingsService';
import UserMenu from '../Auth/UserMenu';

const Header = () => {
  const { currentOrganization } = useAuth();
  const { language, setLanguage, t } = useI18n();
  const { isDark, toggleTheme } = useTheme();
  const { increaseFontSize, decreaseFontSize, isMinLevel, isMaxLevel } = useFontSize();
  const notificationsRef = useRef(null);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notificationHistory, setNotificationHistory] = useState([]);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [notificationsError, setNotificationsError] = useState(null);
  const switchThemeLabel = isDark ? t('header.theme.switchToLight') : t('header.theme.switchToDark');

  const eventLabelByType = {
    risk_critical: t('settings.notifications.history.events.riskCritical'),
    risk_high: t('settings.notifications.history.events.riskHigh'),
    objective_deadline: t('settings.notifications.history.events.objectiveDeadline'),
    stakeholder_change: t('settings.notifications.history.events.stakeholderChange'),
    billing_payment_registered: t('settings.notifications.history.events.billingPaymentRegistered'),
    billing_payment_confirmed: t('settings.notifications.history.events.billingPaymentConfirmed'),
    billing_payment_rejected: t('settings.notifications.history.events.billingPaymentRejected'),
    billing_status_changed: t('settings.notifications.history.events.billingStatusChanged'),
    billing_due_reminder: t('settings.notifications.history.events.billingDueReminder'),
  };

  const statusLabelByType = {
    sent: t('settings.notifications.history.status.sent'),
    failed: t('settings.notifications.history.status.failed'),
    skipped: t('settings.notifications.history.status.skipped'),
    pending: t('settings.notifications.history.status.pending'),
  };

  const statusClassByType = {
    sent: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    skipped: 'bg-slate-100 text-slate-700 dark:bg-slate-700/60 dark:text-slate-200',
    pending: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  };

  const hasAttentionNotifications = notificationHistory.some((item) => item.status === 'pending' || item.status === 'failed');

  const formatWhen = (value) => {
    if (!value) return t('header.notificationsPanel.now');
    try {
      return new Date(value).toLocaleString();
    } catch {
      return value;
    }
  };

  const loadNotificationHistory = async () => {
    if (!currentOrganization?.id) {
      setNotificationHistory([]);
      setNotificationsError(null);
      return;
    }

    setNotificationsLoading(true);
    setNotificationsError(null);
    try {
      const result = await settingsService.getNotificationHistory(currentOrganization.id, 8);
      setNotificationHistory(result.results || []);
    } catch (error) {
      setNotificationsError(t('header.notificationsPanel.historyError'));
      setNotificationHistory([]);
      console.error('Error loading notifications history:', error);
    } finally {
      setNotificationsLoading(false);
    }
  };

  useEffect(() => {
    if (!notificationsOpen) return undefined;

    const handleClickOutside = (event) => {
      if (notificationsRef.current && !notificationsRef.current.contains(event.target)) {
        setNotificationsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [notificationsOpen]);

  useEffect(() => {
    if (notificationsOpen) {
      loadNotificationHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notificationsOpen, currentOrganization?.id]);

  return (
    <header className="bg-white dark:bg-slate-800 shadow-md dark:shadow-slate-900 border-b border-slate-200 dark:border-slate-700 transition-colors duration-300 fixed top-0 left-0 right-0 z-50">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">{t('header.appTitle')}</h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {currentOrganization?.name || t('header.appSubtitleFallback')}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button
              type="button"
              onClick={toggleTheme}
              title={switchThemeLabel}
              aria-label={switchThemeLabel}
              className="p-2 text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-slate-700 rounded-lg transition-colors"
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            {/* Accesibilidad: tamaño de texto */}
            <div className="flex items-center gap-0.5" role="group" aria-label={t('header.accessibility.fontSizeLabel')}>
              <button
                type="button"
                onClick={decreaseFontSize}
                disabled={isMinLevel}
                title={t('header.accessibility.decreaseFont')}
                aria-label={t('header.accessibility.decreaseFont')}
                className="px-2 py-1.5 text-sm font-semibold leading-none text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed select-none"
              >
                A−
              </button>
              <button
                type="button"
                onClick={increaseFontSize}
                disabled={isMaxLevel}
                title={t('header.accessibility.increaseFont')}
                aria-label={t('header.accessibility.increaseFont')}
                className="px-2 py-1.5 text-base font-semibold leading-none text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed select-none"
              >
                A+
              </button>
            </div>

            <select
              aria-label={t('header.languageLabel')}
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              className="px-2 py-1.5 text-xs rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200"
            >
              <option value="es-LATAM">{t('header.languageOptions.es')}</option>
              <option value="en">{t('header.languageOptions.en')}</option>
              <option value="pt">{t('header.languageOptions.pt')}</option>
            </select>

            <div className="relative" ref={notificationsRef}>
              <button
                type="button"
                onClick={() => setNotificationsOpen((prev) => !prev)}
                title={notificationsOpen ? t('header.notificationsPanel.close') : t('header.notificationsPanel.open')}
                aria-label={notificationsOpen ? t('header.notificationsPanel.close') : t('header.notificationsPanel.open')}
                className="relative p-2 text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                <Bell className="w-5 h-5" />
                {hasAttentionNotifications && <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>}
              </button>

              {notificationsOpen && (
                <div
                  className="absolute right-0 mt-2 w-[360px] max-w-[calc(100vw-2rem)] rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-xl overflow-hidden"
                  aria-label={t('header.notificationsPanel.label')}
                >
                  <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{t('header.notifications')}</h3>
                    <span className="text-xs text-slate-500 dark:text-slate-400">{notificationHistory.length}</span>
                  </div>

                  <div className="max-h-80 overflow-y-auto">
                    {notificationsLoading && (
                      <div className="px-4 py-5 text-sm text-slate-500 dark:text-slate-400">{t('header.notificationsPanel.loading')}</div>
                    )}

                    {!notificationsLoading && notificationsError && (
                      <div className="px-4 py-5 text-sm text-red-600 dark:text-red-300">{notificationsError}</div>
                    )}

                    {!notificationsLoading && !notificationsError && notificationHistory.length === 0 && (
                      <div className="px-4 py-5 text-sm text-slate-500 dark:text-slate-400">{t('settings.notifications.history.empty')}</div>
                    )}

                    {!notificationsLoading && !notificationsError && notificationHistory.map((item) => (
                      <div
                        key={item.id}
                        className="px-4 py-3 border-b border-slate-100 dark:border-slate-700/60 last:border-b-0"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                              {eventLabelByType[item.event_type] || item.event_type}
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{item.subject}</p>
                            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                              {Array.isArray(item.recipients) && item.recipients.length > 0
                                ? item.recipients.join(', ')
                                : t('header.notificationsPanel.noRecipients')}
                            </p>
                          </div>
                          <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${statusClassByType[item.status] || statusClassByType.pending}`}>
                            {statusLabelByType[item.status] || item.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-2">{formatWhen(item.sent_at || item.created_at)}</p>
                      </div>
                    ))}
                  </div>

                  <div className="px-4 py-2 bg-slate-50 dark:bg-slate-800/80 text-right">
                    <Link
                      to="/settings"
                      onClick={() => setNotificationsOpen(false)}
                      className="text-xs font-medium text-blue-600 dark:text-blue-300 hover:underline"
                    >
                      {t('header.settings')}
                    </Link>
                  </div>
                </div>
              )}
            </div>

            <Link 
              to="/settings"
              className="p-2 text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-slate-700 rounded-lg transition-colors"
            >
              <Settings className="w-5 h-5" />
            </Link>

            <UserMenu />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;