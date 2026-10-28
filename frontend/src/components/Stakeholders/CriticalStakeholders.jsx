import React from 'react';
import { AlertTriangle, TrendingUp, Users, Activity } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const CriticalStakeholders = ({ stakeholders, loading }) => {
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!stakeholders || stakeholders.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <h3 className="text-lg font-semibold dark:text-white mb-4 flex items-center">
          <Users className="mr-2 h-5 w-5" />
          {t('stakeholdersInsights.critical.title')}
        </h3>
        <p className="text-slate-500 dark:text-slate-400 text-center py-8">
          {t('stakeholdersInsights.critical.empty')}
        </p>
      </div>
    );
  }

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'CRÍTICO': return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700';
      case 'ALTO': return 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300 border-orange-300 dark:border-orange-700';
      case 'MEDIO': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700';
      default: return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-700';
    }
  };

  const getInfluenceColor = (score) => {
    if (score >= 0.8) return 'text-red-600 dark:text-red-400';
    if (score >= 0.6) return 'text-orange-600 dark:text-orange-400';
    return 'text-yellow-600 dark:text-yellow-400';
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <h3 className="text-lg font-semibold dark:text-white mb-4 flex items-center">
        <AlertTriangle className="mr-2 h-5 w-5 text-red-500" />
        {t('stakeholdersInsights.critical.title')} ({stakeholders.length})
      </h3>

      <div className="space-y-4">
        {stakeholders.map((sh) => (
          <div
            key={sh.stakeholder_id || sh.id}
            className={`border-l-4 rounded-lg p-4 ${getRiskColor(sh.risk_level)} transition-all hover:shadow-md`}
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <h4 className="font-semibold dark:text-slate-100">{sh.name}</h4>
                <p className="text-sm dark:text-slate-400 capitalize">{sh.type}</p>
              </div>
              <div className="flex flex-col items-end">
                <span className={`text-2xl font-bold ${getInfluenceColor(sh.composite_score)}`}>
                  {(sh.composite_score * 100).toFixed(0)}%
                </span>
                <span className="text-xs dark:text-slate-400">{t('stakeholdersInsights.critical.influence')}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-3">
              <div className="flex items-center text-sm">
                <TrendingUp className="h-4 w-4 mr-1 dark:text-slate-400" />
                <span className="dark:text-slate-300">{t('stakeholdersInsights.critical.powerLabel')}</span>
                <span className="ml-1 font-medium capitalize dark:text-slate-200">{sh.power}</span>
              </div>
              <div className="flex items-center text-sm">
                <Activity className="h-4 w-4 mr-1 text-slate-500 dark:text-slate-400" />
                <span className="text-slate-600 dark:text-slate-400">{t('stakeholdersInsights.critical.interestLabel')}</span>
                <span className="ml-1 font-medium capitalize">{sh.interest}</span>
              </div>
            </div>

            {sh.engagement_strategy && (
              <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                <p className="text-sm text-slate-700 dark:text-slate-300">
                  <span className="font-medium">{t('stakeholdersInsights.critical.strategyLabel')}</span> {sh.engagement_strategy}
                </p>
              </div>
            )}

            <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
              <span className="text-xs font-medium px-2 py-1 rounded bg-slate-100 dark:bg-slate-700 dark:text-slate-300">
                {sh.is_hub && t('stakeholdersInsights.critical.tags.hub')} {sh.is_broker && t('stakeholdersInsights.critical.tags.broker')}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {sh.connections} {t('stakeholdersInsights.critical.connections')}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CriticalStakeholders;