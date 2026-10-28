import React from 'react';
import { Package, Briefcase, Settings, AlertCircle, Target, Users } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const ProcessList = ({ processesByType, loading }) => {
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

  if (!processesByType) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <p className="text-slate-500 dark:text-slate-400 text-center py-8">{t('processList.empty')}</p>
      </div>
    );
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'strategic': return <Target className="h-5 w-5" />;
      case 'operational': return <Briefcase className="h-5 w-5" />;
      case 'support': return <Settings className="h-5 w-5" />;
      default: return <Package className="h-5 w-5" />;
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'strategic': return 'border-purple-200 dark:border-purple-700 bg-purple-50 dark:bg-purple-900/30';
      case 'operational': return 'border-blue-200 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/30';
      case 'support': return 'border-green-200 dark:border-green-700 bg-green-50 dark:bg-green-900/30';
      default: return 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700';
    }
  };

  const getTypeBadgeColor = (type) => {
    switch (type) {
      case 'strategic': return 'bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-300';
      case 'operational': return 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300';
      case 'support': return 'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-300';
      default: return 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-300';
    }
  };

  const typeNames = {
    strategic: t('processList.types.strategic'),
    operational: t('processList.types.operational'),
    support: t('processList.types.support'),
  };

  return (
    <div className="space-y-6">
      {Object.entries(processesByType).map(([type, processes]) => (
        <div key={type} className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center mb-4">
            <div className={`p-2 rounded-lg ${getTypeBadgeColor(type)} mr-3`}>
              {getTypeIcon(type)}
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
              {typeNames[type]} ({processes.length})
            </h3>
          </div>

          {processes.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {processes.map((process) => (
                <div
                  key={process.id}
                  className={`border-2 rounded-lg p-4 ${getTypeColor(type)} hover:shadow-md dark:hover:shadow-slate-900/50 transition-all`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <span className="font-mono text-sm font-semibold text-slate-700 dark:text-slate-300 mr-2">
                          {process.code}
                        </span>
                        {process.is_critical && (
                          <span className="flex items-center text-xs bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 px-2 py-0.5 rounded transition-colors">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            {t('processList.criticalBadge')}
                          </span>
                        )}
                      </div>
                      <h4 className="font-semibold text-slate-900 dark:text-white mt-1">
                        {process.name}
                      </h4>
                    </div>
                  </div>

                  {process.objective && (
                    <p className="text-sm text-slate-700 dark:text-slate-300 mb-3 line-clamp-2">
                      {process.objective}
                    </p>
                  )}

                  <div className="flex items-center text-sm text-slate-600 dark:text-slate-400 mb-2">
                    <Users className="h-4 w-4 mr-1" />
                    <span className="font-medium">{t('processList.fields.responsible')}:</span>
                    <span className="ml-1">{process.owner}</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 dark:text-slate-400">
                    <div>
                      <span className="font-medium">{t('processList.fields.inputs')}:</span> {process.inputs?.length || 0}
                    </div>
                    <div>
                      <span className="font-medium">{t('processList.fields.outputs')}:</span> {process.outputs?.length || 0}
                    </div>
                    <div>
                      <span className="font-medium">{t('processList.fields.kpis')}:</span> {process.kpis?.length || 0}
                    </div>
                    <div>
                      <span className="font-medium">{t('processList.fields.activities')}:</span> {process.activities_count || 0}
                    </div>
                  </div>

                  {process.criticality_score !== undefined && (
                    <div className="mt-3 pt-3 border-t dark:border-slate-700">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-600 dark:text-slate-400">{t('processList.fields.criticality')}:</span>
                        <div className="flex items-center">
                          <div className="w-24 h-2 bg-slate-200 dark:bg-slate-700 rounded-full mr-2">
                            <div
                              className={`h-2 rounded-full ${
                                process.criticality_score >= 0.7 ? 'bg-red-500' :
                                process.criticality_score >= 0.5 ? 'bg-yellow-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${process.criticality_score * 100}%` }}
                            />
                          </div>
                          <span className="font-semibold text-slate-700 dark:text-slate-300">
                            {(process.criticality_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-500 dark:text-slate-400 text-sm italic">{t('processList.emptyByCategory')}</p>
          )}
        </div>
      ))}
    </div>
  );
};

export default ProcessList;