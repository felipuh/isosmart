import React from 'react';
import { useI18n } from '../../context/I18nContext';

const RiskStats = ({ stats, onRefresh }) => {
  const { t } = useI18n();
  if (!stats) return null;

  const levelColors = {
    critico: { bg: 'bg-red-100', text: 'text-red-800' },
    alto: { bg: 'bg-orange-100', text: 'text-orange-800' },
    medio: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
    bajo: { bg: 'bg-green-100', text: 'text-green-800' },
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-blue-100 dark:bg-blue-900/40 rounded-full p-3">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-4">
                    <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{t('riskManagement.stats.totalRisks')}</p>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">{stats.total_risks || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-yellow-100 dark:bg-yellow-900/40 rounded-full p-3">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="ml-4">
                    <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{t('riskManagement.stats.active')}</p>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">{stats.active_risks || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-red-100 dark:bg-red-900/40 rounded-full p-3">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
                    <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{t('riskManagement.stats.critical')}</p>
              <p className="text-2xl font-semibold text-red-600">{stats.by_level?.critico || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-green-100 dark:bg-green-900/40 rounded-full p-3">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
                    <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{t('riskManagement.stats.mitigated')}</p>
              <p className="text-2xl font-semibold text-green-600">{stats.by_status?.mitigated || 0}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
                <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-4">{t('riskManagement.stats.distributionByLevel')}</h3>
          <div className="space-y-4">
            {Object.entries(levelColors).map(([level, colors]) => {
              const count = stats.by_level?.[level] || 0;
              const percentage = stats.active_risks ? ((count / stats.active_risks) * 100).toFixed(1) : 0;
                    const labels = {
                      critico: t('riskManagement.levels.critico'),
                      alto: t('riskManagement.levels.alto'),
                      medio: t('riskManagement.levels.medio'),
                      bajo: t('riskManagement.levels.bajo'),
                    };
              return (
                <div key={level}>
                  <div className="flex justify-between items-center mb-1">
                    <span className={`text-sm font-medium ${colors.text}`}>{labels[level]}</span>
                    <span className="text-sm text-gray-500">{count} ({percentage}%)</span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2.5">
                    <div className={`h-2.5 rounded-full ${colors.bg.replace('100', '500')}`} style={{ width: `${percentage}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
                <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-4">{t('riskManagement.stats.byAiModule')}</h3>
          <div className="grid grid-cols-2 gap-4">
            {[
                    { source: 'SCA', label: t('riskManagement.stats.modules.sca'), icon: '🔍' },
                    { source: 'SIE', label: t('riskManagement.stats.modules.sie'), icon: '👥' },
                    { source: 'SPM', label: t('riskManagement.stats.modules.spm'), icon: '⚙️' },
                    { source: 'MANUAL', label: t('riskManagement.stats.modules.manual'), icon: '✏️' }
            ].map(({ source, label, icon }) => (
              <div key={source} className="bg-slate-50 dark:bg-slate-700 rounded-lg p-4 text-center">
                <div className="text-2xl mb-2">{icon}</div>
                <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">{label}</div>
                <div className="text-xl font-bold text-slate-900 dark:text-white">{stats.by_source?.[source] || 0}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button onClick={onRefresh} className="inline-flex items-center px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-md shadow-sm text-sm font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700">
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
                {t('riskManagement.dashboard.buttons.refresh')}
        </button>
      </div>
    </div>
  );
};

export default RiskStats;