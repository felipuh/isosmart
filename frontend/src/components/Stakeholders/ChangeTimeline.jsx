import React from 'react';
import { Clock, AlertCircle, TrendingDown, TrendingUp, Activity } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const ChangeTimeline = ({ changes, loading }) => {
  const { t, language } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!changes || changes.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <h3 className="text-lg font-semibold dark:text-white mb-4 flex items-center">
          <Clock className="mr-2 h-5 w-5" />
          {t('changeTimeline.titleRecent')}
        </h3>
        <p className="text-slate-500 dark:text-slate-400 text-center py-8">{t('changeTimeline.empty')}</p>
      </div>
    );
  }

  const getChangeIcon = (changeType) => {
    if (changeType.includes('alto')) return <AlertCircle className="h-5 w-5 text-red-500" />;
    if (changeType.includes('drop')) return <TrendingDown className="h-5 w-5 text-red-500" />;
    if (changeType.includes('increase')) return <TrendingUp className="h-5 w-5 text-green-500" />;
    return <Activity className="h-5 w-5 text-blue-500" />;
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'alto': return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700';
      case 'medio': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700';
      case 'bajo': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-700';
      default: return 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-600';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return t('changeTimeline.timeAgoMinutes').replace('{count}', diffMins);
    if (diffHours < 24) return t('changeTimeline.timeAgoHours').replace('{count}', diffHours);
    if (diffDays < 7) return t('changeTimeline.timeAgoDays').replace('{count}', diffDays);
    return date.toLocaleDateString(language === 'es-LATAM' ? 'es-ES' : language, { day: '2-digit', month: 'short', year: 'numeric' });
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <h3 className="text-lg font-semibold dark:text-white mb-4 flex items-center">
        <Clock className="mr-2 h-5 w-5 text-blue-500" />
        {t('changeTimeline.titleRecent')} ({changes.length})
      </h3>

      <div className="space-y-4">
        {changes.slice(0, 10).map((change, index) => (
          <div
            key={index}
            className="border-l-4 border-slate-300 dark:border-slate-600 pl-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors rounded"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <div className="mt-1">{getChangeIcon(change.change_type)}</div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-semibold dark:text-slate-100">{change.stakeholder_name}</h4>
                    {change.severity && (
                      <span className={`text-xs px-2 py-1 rounded border ${getSeverityColor(change.severity)}`}>
                        {change.severity.toUpperCase()}
                      </span>
                    )}
                  </div>
                  
                  {change.new_expectations && change.new_expectations.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm dark:text-slate-300">{t('changeTimeline.newExpectations')}</p>
                      <ul className="list-disc list-inside text-sm dark:text-slate-400">
                        {change.new_expectations.map((exp, idx) => (
                          <li key={idx}>{exp}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {change.removed_expectations && change.removed_expectations.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm dark:text-slate-300">{t('changeTimeline.removedExpectations')}</p>
                      <ul className="list-disc list-inside text-sm dark:text-slate-500 line-through">
                        {change.removed_expectations.map((exp, idx) => (
                          <li key={idx}>{exp}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {change.recommendation && (
                    <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/30 rounded text-sm dark:text-blue-300">
                      💡 {t('changeTimeline.recommendation')} {change.recommendation}
                    </div>
                  )}
                </div>
              </div>
              
              <span className="text-xs dark:text-slate-400 whitespace-nowrap ml-4">
                {formatDate(change.change_date)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChangeTimeline;