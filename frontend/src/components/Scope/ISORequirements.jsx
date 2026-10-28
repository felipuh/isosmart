import React from 'react';
import { CheckCircle2, Circle, AlertCircle } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const ISORequirements = ({ requirements, loading }) => {
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!requirements) {
    return null;
  }

  const applicableReqs = requirements.requirements || [];
  const coverage = requirements.coverage || 0;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold dark:text-white">{t('isoRequirements.title')}</h3>
        <div className="flex items-center">
          <div className="text-right mr-4">
            <p className="text-sm text-slate-600 dark:text-slate-400">{t('isoRequirements.coverage')}</p>
            <p className="text-2xl font-bold text-green-600">{coverage.toFixed(0)}%</p>
          </div>
          <div className="w-16 h-16">
            <svg className="transform -rotate-90" viewBox="0 0 36 36">
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#475569"
                strokeWidth="3"
              />
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#10b981"
                strokeWidth="3"
                strokeDasharray={`${coverage}, 100`}
              />
            </svg>
          </div>
        </div>
      </div>

      {applicableReqs.length > 0 ? (
        <div className="space-y-3">
          {applicableReqs.map((req, idx) => (
            <div
              key={idx}
              className="border border-green-200 dark:border-green-700 bg-green-50 dark:bg-green-900/30 rounded-lg p-4 flex items-start transition-colors"
            >
              <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mr-3 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-semibold text-slate-900 dark:text-white">
                    {t('isoRequirements.clauseLabel').replace('{clause}', req.clause).replace('{title}', req.title)}
                  </h4>
                  <span className="text-xs bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-300 px-2 py-1 rounded transition-colors">
                    {t('isoRequirements.applicableStatus')}
                  </span>
                </div>
                {req.justification && (
                  <p className="text-sm text-slate-700 dark:text-slate-300 mt-1">
                    {req.justification}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-slate-500 dark:text-slate-400 text-center py-8">
          {t('isoRequirements.noRequirementsDefined')}
        </p>
      )}
    </div>
  );
};

export default ISORequirements;